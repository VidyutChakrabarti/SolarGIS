import pandas as pd 

def alter_df(df):
        
    if 'rect_height' not in df.columns or 'line_height' not in df.columns:
        raise ValueError("DataFrame must contain 'rect_height' and 'line_height' columns.")
    
    df['estimated_height'] = df['rect_height'] / df['line_height']
    
    return df

def combine_dataframes(dfs):
    combined_data = {
        'latitudes': [],
        'longitudes': [],
        'estimated_height': []
    }

    for df in dfs:
        for _, row in df.iterrows():
            coords = row['bbox_coords']  
            latitudes = [coord[1] for polygon in coords for coord in polygon]  
            longitudes = [coord[0] for polygon in coords for coord in polygon] 
            
            combined_data['latitudes'].append(latitudes)
            combined_data['longitudes'].append(longitudes)
            combined_data['estimated_height'].append(row['estimated_height'])

    combined_df = pd.DataFrame(combined_data)
    return combined_df