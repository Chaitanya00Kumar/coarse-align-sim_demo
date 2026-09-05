import pygame, sys, os, shutil, cv2, numpy as np
from disturbance import add_disturbance

ENABLE_DISTURBANCE = True

SIM_WIDTH, SIM_HEIGHT = 640, 480   # size of the actual simulated "camera feed"

pygame.init()
screen = pygame.display.set_mode((SIM_WIDTH * 2, SIM_HEIGHT))   # double-wide: clean | disturbed
scene_surface = pygame.Surface((SIM_WIDTH, SIM_HEIGHT))          # the real scene, drawn separately

script_dir = os.path.dirname(os.path.abspath(__file__))
frames_dir = os.path.join(script_dir, "frames")
shutil.rmtree(frames_dir, ignore_errors=True)
os.makedirs(frames_dir)

clock = pygame.time.Clock()
target_pos = [100.0, 240.0]
velocity = [2.5, 1.2]
frame_count = 0
max_frames = 300

with open(os.path.join(script_dir, "ground_truth.csv"), "w") as gt_file:
    gt_file.write("frame,true_x,true_y\n")

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        if frame_count == max_frames:
            print("MAX LIMIT OF 300 FRAMES REACHED")
            pygame.quit()
            sys.exit()

        frame_count += 1

        if not (0 < target_pos[0] < SIM_WIDTH):
            velocity[0] *= -1
        if not (0 < target_pos[1] < SIM_HEIGHT):
            velocity[1] *= -1
        target_pos[0] += velocity[0]
        target_pos[1] += velocity[1]

        # --- draw the CLEAN scene onto its own surface, not the window directly ---
        scene_surface.fill((20, 20, 30))
        pygame.draw.circle(scene_surface, (255, 0, 0), (int(target_pos[0]), int(target_pos[1])), 5)

        # --- left panel: clean feed ---
        screen.blit(scene_surface, (0, 0))

        # --- build the disturbed version from that same scene ---
        frame_array = pygame.surfarray.array3d(scene_surface)
        frame_array = np.transpose(frame_array, (1, 0, 2))
        frame_array = cv2.cvtColor(frame_array, cv2.COLOR_RGB2BGR)
        frame_array = add_disturbance(frame_array, ENABLE_DISTURBANCE)

        # --- right panel: disturbed feed, converted back so pygame can display it ---
        display_array = cv2.cvtColor(frame_array, cv2.COLOR_BGR2RGB)
        display_array = np.transpose(display_array, (1, 0, 2))
        disturbed_surface = pygame.surfarray.make_surface(display_array)
        screen.blit(disturbed_surface, (SIM_WIDTH, 0))

        pygame.display.flip()

        # --- save the disturbed frame: this is the "camera feed" your teammate's tracker reads ---
        cv2.imwrite(os.path.join(frames_dir, f"frame_{frame_count:04d}.png"), frame_array)
        gt_file.write(f"{frame_count},{int(target_pos[0])},{int(target_pos[1])}\n")

        clock.tick(60)
