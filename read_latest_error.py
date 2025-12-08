
try:
    with open('logs/paas.log', 'r') as f:
        lines = f.readlines()
        
    # Find lines with "Deployment command failed" and print context
    # Search in reverse to find the latest
    found = False
    for i in range(len(lines) - 1, -1, -1):
        if "Deployment command failed" in lines[i]:
            found = True
            print(f"--- FAILED AT LINE {i} ---")
            # Print 50 lines before and 20 lines after (or until end)
            start = max(0, i - 50)
            end = min(len(lines), i + 20)
            for j in range(start, end):
                print(lines[j].strip())
            print("-----------------------")
            break # Only print the latest one
            
    if not found:
        print("Error message not found in logs. Printing last 50 lines:")
        for line in lines[-50:]:
            print(line.strip())
            
except Exception as e:
    print(f"Error reading log: {e}")
