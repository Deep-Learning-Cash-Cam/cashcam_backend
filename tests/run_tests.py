import os
import subprocess
import sys
from app.core.config import settings

def run_tests():
    os.makedirs('tests', exist_ok=True)
    
    # Run pytest and capture output
    result = subprocess.run(
        ['pytest', '-v'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    with open(settings.TEST_OUTPUT_PATH, 'w') as f:
        f.write(result.stdout)
    
    print(result.stdout)
    return result.returncode

if __name__ == '__main__':
    sys.exit(run_tests())