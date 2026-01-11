import pandas as pd

AUTOSOMES = [str(i) for i in range(1, 23)]
GONOSOMES = ['23', '24']
CHROMOSOMES = AUTOSOMES + GONOSOMES

MOSAIC_THRESHOLD = 0.45  # Ngưỡng xác định Gain/Loss từ bình thường

def determine_gender(bluefuse_df: pd.DataFrame) -> str:
    """Xác định giới tính dựa trên NST Y của BlueFuse."""
    if bluefuse_df.empty:
        return 'Unknown'
    
    # Đảm bảo cột chrom là string để so sánh chính xác
    bluefuse_df = bluefuse_df.copy()
    bluefuse_df['chrom'] = bluefuse_df['chrom'].astype(str)
        
    y_data = bluefuse_df[bluefuse_df['chrom'] == '24']
    if y_data.empty:
        return 'Female'
    
    y_data = y_data.copy()
    y_data['length'] = y_data['chromEnd'] - y_data['chromStart']
    longest_y = y_data.loc[y_data['length'].idxmax()]
    copy_number_y = longest_y['copyNumber']
    
    return 'Female' if copy_number_y < MOSAIC_THRESHOLD else 'Male'

def get_expected_copy_number(chromosome: str, gender: str) -> float:
    """Trả về giá trị CN bình thường dự kiến cho một NST."""
    if chromosome in AUTOSOMES:
        return 2.0
    elif chromosome == '23':  # X
        return 2.0 if gender == 'Female' else 1.0
    elif chromosome == '24':  # Y
        return 0.0 if gender == 'Female' else 1.0
    return 2.0