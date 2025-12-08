
import re

try:
    with open('logs/paas.log', 'r') as f:
        lines = f.readlines()
        
    found = False
    for i in range(len(lines) - 1, -1, -1):
        if "Command failed with exit code" in lines[i]:
            found = True
            print(f"--- FAILED COMMAND AT LINE {i} ---")
            # Print context
            start = max(0, i - 20)
            end = min(len(lines), i + 10)
            for j in range(start, end):
                print(lines[j].strip())
            print("-----------------------")
            break
            
    if not found:
        # Fallback to looking for "Deployment command failed"
        for i in range(len(lines) - 1, -1, -1):
             if "Deployment command failed" in lines[i]:
                found = True
                print(f"--- DEPLOYMENT FAILED AT LINE {i} ---")
                start = max(0, i - 20)
                end = min(len(lines), i + 10)
                for j in range(start, end):
                    print(lines[j].strip())
                break

except Exception as e:
    print(f"Error reading log: {e}")
