import subprocess
import sys

scenarios = ['baseline', 'noise', 'jitter', 'blur', 'occlusion', 'dynamic_velocity']

print('==========================================')
print('       EXECUTING 6-SCENARIO TEST MATRIX')
print('==========================================')

for scenario in scenarios:
    print(f'\n--- Running Scenario: [{scenario}] ---')
    subprocess.run([sys.executable, 'scene_simulator.py', '--scenario', scenario], check=True)
    subprocess.run([sys.executable, 'detector.py'], check=True)
    subprocess.run([sys.executable, 'tracker.py'], check=True)

print('\n--- Compiling Final Performance Matrix ---')
subprocess.run([sys.executable, 'performance_analyser.py'], check=True)
print('\nTest matrix execution completed successfully!')
