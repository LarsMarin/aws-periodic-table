# Funktion zum Berechnen der Elementpositionen in der Tabelle
def compute_positions(periodic):
    # Vertical order for topmost rows
    vlayout = [
        [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1],
        [1,1,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1],
        [1,1,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1],
        [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
        [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
        [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
        [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
        [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
        [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    ]
    vlayout = list(zip(*vlayout)) # transpose for easier handling
    
    # Horizontal layout for bottom 3+ rows
    hlayout = [
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
        [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
    ]
    
    indices = []
    hrow = 0
    for row in range(0,len(vlayout)):
        for col in range(0, len(vlayout[row])):
            if vlayout[row][col]:
                indices.append([hrow+col+1, row+1])
                
    hrow = col + 2
    for row in range(0,len(hlayout)):
        for col in range(0, len(hlayout[row])):
            if hlayout[row][col]:
                indices.append([hrow+row+1, col+1])
    
    # Ensure we have enough indices for all services
    total_services = sum(len(cat.get("services", [])) for cat in periodic['categories'])
    if total_services > len(indices):
        extra = total_services - len(indices)
        # Determine starting row after the predefined layout
        start_row = (indices[-1][0] + 1) if indices else 1
        # Fill extra indices row-wise across 19 columns per row
        COLS = 19
        for i in range(extra):
            row = start_row + (i // COLS)
            col = (i % COLS) + 1
            indices.append([row, col])
    
    # Assign computed positions
    count = 0
    for category in periodic['categories']:
        for service in category["services"]:
            service['row'] = indices[count][0]
            service['column'] = indices[count][1]
            count = count + 1
    
    # Compute required grid rows for template (at least 18 to preserve original look)
    periodic['grid_rows'] = max(18, max((pos[0] for pos in indices[:total_services]), default=18))
    
    return periodic
