import pygame, sys, os, shutil, cv2, numpy as np
from disturbance import add_disturbance


ENABLE_DISTURBANCE = True

pygame.init()
screen = pygame.display.set_mode((640, 480))   # opens the window
script_dir = os.path.dirname(os.path.abspath(__file__))
frames_dir = os.path.join(script_dir, "frames")

shutil.rmtree(frames_dir, ignore_errors=True)
os.makedirs(frames_dir)
print("***Folder created:", os.path.exists("frames"))
print(os.getcwd())
clock = pygame.time.Clock()                     # controls frame speed
target_pos = [100.0, 240.0]
velocity = [2.5, 1.2]
frame_count = 0
max_frames = 300
with open(os.path.join(script_dir, "ground_truth.csv"), "w") as gt_file:
    gt_file.write("frame,true_x,true_y\n")

    while True:
        for event in pygame.event.get():            # step 1: check what happened
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        if frame_count == max_frames:
            print("MAX LIMIT OF 300 FRAMES REACHED")
            pygame.quit()
            sys.exit()

        width, height = screen.get_size()

        frame_count += 1

        

        if not (0 < target_pos[0] < width):
            velocity[0] *= -1
        if not (0 < target_pos[1] < height):
            velocity[1] *= -1

        target_pos[0] += velocity[0]
        target_pos[1] += velocity[1]

        # step 2: update stuff (nothing yet)

        screen.fill((20, 20, 30))                   # step 3: redraw — wipe screen to dark blue-grey
        pygame.draw.circle(screen, (255, 0, 0), (int(target_pos[0]), int(target_pos[1])), 5.5)
        pygame.display.flip()                       # step 4: show the new frame

        frame_array = pygame.surfarray.array3d(screen)              # pygame surface -> numpy array (width, height, 3), RGB
        frame_array = np.transpose(frame_array, (1, 0, 2))            # fix axis order -> (height, width, 3)
        frame_array = cv2.cvtColor(frame_array, cv2.COLOR_RGB2BGR)     # fix color order for OpenCV
        frame_array = add_disturbance(frame_array, ENABLE_DISTURBANCE)
        cv2.imwrite(os.path.join(frames_dir, f"frame_{frame_count:04d}.png"), frame_array)

        gt_file.write(f"{frame_count},{int(target_pos[0])},{int(target_pos[1])}\n")
        print("***Saved frame", frame_count)
        clock.tick(60)                               # step 5: cap at 60 frames per second
