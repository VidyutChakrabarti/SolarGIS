def alter_df(df):
    # Ensure there are an equal number of 'rect' and 'line' rows
    rect_rows = df[df['type'] == 'rect'].reset_index(drop=True)
    line_rows = df[df['type'] == 'line'].reset_index(drop=True)
    
    if len(rect_rows) != len(line_rows):
        raise ValueError("Unequal number of 'rect' and 'line' entries")
    
    for i in range(len(rect_rows)):
        rect = rect_rows.loc[i]
        line = line_rows.loc[i]
        
        # Calculate the height of the line as proportional to 1 meter
        line_height = line['height']
        rect_h_in_meters = rect['height'] / line_height
        rect_w_in_m = rect['width'] / line_height
        
        # Store the calculated meter height in the 'rect' row
        df.loc[rect_rows.index[i], 'estimated_height'] = rect_h_in_meters
        df.loc[rect_rows.index[i], 'estimated_width'] = rect_w_in_m
    
    # Drop all rows where 'type' is 'line'
    df = df[df['type'] != 'line'].reset_index(drop=True)
    
    return df
