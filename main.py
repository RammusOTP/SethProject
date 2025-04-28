import pandas as pd
import matplotlib.pyplot as plt
import os
import seaborn as sns

# Column mapping for FY23 and FY24 data
fy23_columns_map = {
    'Date': 'Date',
    'FY': 'FY',
    'Item Desc': 'Item',
    'Cost': 'Cost',
    'Cost Center Level 5': 'Global Line of Service',
    'Cost Center Level 4': 'UK Line of Service',
    'Management Level': 'Management Level',
    'Machine': 'Machine'
}

fy24_columns_map = {
    'Date': 'Date',
    'FY': 'FY',
    'Item': 'Item',
    'Cost': 'Cost',
    'Global Line of Service': 'Global Line of Service',
    'UK Line of Service': 'UK Line of Service',
    'Management Level': 'Management Level',
    'Machine': 'Machine'
}

# Load and preprocess the FY23 data
df_fy23 = pd.read_csv(r'data/Tech Vend data FY23 Anon.csv')
df_fy23.columns = df_fy23.columns.str.strip()
df_fy23 = df_fy23[list(fy23_columns_map.keys())].rename(columns=fy23_columns_map)
df_fy23['Date'] = pd.to_datetime(df_fy23['Date'], format='%d/%m/%Y', errors='coerce')

# Load and preprocess the FY24 data
df_fy24 = pd.read_csv(r'data/Tech Vend data FY24 Anon.csv')
df_fy24.columns = df_fy24.columns.str.strip()
df_fy24 = df_fy24[list(fy24_columns_map.keys())].rename(columns=fy24_columns_map)
df_fy24['Date'] = pd.to_datetime(df_fy24['Date'], format='%m/%d/%Y', errors='coerce')
df_fy24['Date'] = df_fy24['Date'].dt.strftime('%d/%m/%Y')
df_fy24['Date'] = pd.to_datetime(df_fy24['Date'], format='%d/%m/%Y', errors='coerce')

# Combine the datasets and preprocess the Cost column
combined_df = pd.concat([df_fy23, df_fy24], ignore_index=True)
combined_df['Cost'] = combined_df['Cost'].astype(str).replace({'£': '', ',': ''}, regex=True).str.strip()
combined_df['Cost'] = pd.to_numeric(combined_df['Cost'], errors='coerce')

# Extract date-related components
combined_df['Year'] = combined_df['Date'].dt.year
combined_df['Month'] = combined_df['Date'].dt.month
combined_df['Week'] = combined_df['Date'].dt.isocalendar().week
combined_df['Day of Week'] = combined_df['Date'].dt.dayofweek

# Calculate sales counts for different time frames
sales_counts_all = combined_df.groupby('Date').size().reset_index(name='Sales Count')
weekdays_filtered = [0, 1, 2, 3, 4]  # Weekdays
sales_counts_weekdays_filtered = combined_df[combined_df['Day of Week'].isin(weekdays_filtered)].groupby('Date').size().reset_index(name='Sales Count')
twt_days = [1, 2, 3]  # Tuesday, Wednesday, Thursday
sales_counts_twt = combined_df[combined_df['Day of Week'].isin(twt_days)].groupby('Date').size().reset_index(name='Sales Count')

# Calculate mean and std for sales counts
mean_sales_all = sales_counts_all['Sales Count'].mean()
std_sales_all = sales_counts_all['Sales Count'].std()

mean_sales_weekdays_filtered = sales_counts_weekdays_filtered['Sales Count'].mean()
std_sales_weekdays_filtered = sales_counts_weekdays_filtered['Sales Count'].std()

mean_sales_twt = sales_counts_twt['Sales Count'].mean()
std_sales_twt = sales_counts_twt['Sales Count'].std()

# Calculate rolling statistics
def calc_rolling_stats(df):
    df['Rolling Mean'] = df['Sales Count'].rolling(window=90).mean().ffill()
    df['Rolling Std'] = df['Sales Count'].rolling(window=90).std().ffill()
    return df

sales_counts_all = calc_rolling_stats(sales_counts_all)
sales_counts_weekdays_filtered = calc_rolling_stats(sales_counts_weekdays_filtered)
sales_counts_twt = calc_rolling_stats(sales_counts_twt)

# Create 'images' directory to save plots
if not os.path.exists('images'):
    os.makedirs('images')

# Function to plot sales counts with flat bar chart
def plot_sales_counts_flat(sales_data, title, save_path, mean, std):
    plt.figure(figsize=(12, 6))
    bar_colors = []
    red_bar_count = 0
    yellow_bar_count = 0

    for count in sales_data['Sales Count']:
        if count > mean + std or count < mean - std:
            bar_colors.append('#e0301e')  # Red
            red_bar_count += 1
        else:
            bar_colors.append('#ffb600')  # Yellow
            yellow_bar_count += 1

    plt.bar(sales_data['Date'], sales_data['Sales Count'], color=bar_colors)
    plt.axhline(y=mean, color='#e0301e', linestyle='--', label='Mean')
    plt.axhline(y=mean + std, color='#9013fe', linestyle='--', label='Mean + 1 Std Dev')
    plt.axhline(y=mean - std, color='#9013fe', linestyle='--', label='Mean - 1 Std Dev')
    plt.xticks(rotation=45, ha='right')
    plt.xlabel('Date', fontsize=14)
    plt.ylabel('Sales Count', fontsize=14)
    plt.title(title, fontsize=16)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.legend()
    plt.tight_layout()
    plt.savefig(save_path, format='png')
    plt.close()

    return red_bar_count, yellow_bar_count, mean, std

# Function to plot sales counts with rolling statistics
def plot_sales_counts_rolling(sales_data, title, save_path):
    plt.figure(figsize=(12, 6))
    bar_colors = []
    red_bar_count = 0
    yellow_bar_count = 0

    for index, row in sales_data.iterrows():
        count = row['Sales Count']
        rolling_mean = row['Rolling Mean']
        rolling_std = row['Rolling Std']

        if count > rolling_mean + rolling_std or count < rolling_mean - rolling_std:
            bar_colors.append('#e0301e')  # Red
            red_bar_count += 1
        else:
            bar_colors.append('#ffb600')  # Yellow
            yellow_bar_count += 1

    plt.bar(sales_data['Date'], sales_data['Sales Count'], color=bar_colors)

    # Plot the rolling mean and std fill
    plt.plot(sales_data['Date'], sales_data['Rolling Mean'], color='#9013fe', label='90-Day Rolling Mean', linewidth=2)
    plt.fill_between(sales_data['Date'],
                     sales_data['Rolling Mean'] + sales_data['Rolling Std'],
                     sales_data['Rolling Mean'] - sales_data['Rolling Std'],
                     color='#0089eb', alpha=0.2, label='90-Day Rolling Std Dev')

    plt.xticks(rotation=45, ha='right')
    plt.xlabel('Date', fontsize=14)
    plt.ylabel('Sales Count', fontsize=14)
    plt.title(title, fontsize=16)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.legend()
    plt.tight_layout()
    plt.savefig(save_path, format='png')
    plt.close()

    return red_bar_count, yellow_bar_count, sales_data['Sales Count'].mean(), sales_data['Sales Count'].std()

# Helper function to calculate the red to yellow ratio
def calculate_red_yellow_ratio(red_count, yellow_count):
    if yellow_count == 0:  # Avoid division by zero
        return None  # Or use a different approach to represent no yellow counts
    return (red_count / yellow_count) * 100  # Percentage

# Prepare to collect red and yellow counts
red_yellow_counts = []

# Plotting sales counts
red_count, yellow_count, avg, std = plot_sales_counts_flat(
    sales_counts_all, 
    'Sales Count per Day',
    'images/sales_count_per_day_flat.png',
    mean_sales_all, 
    std_sales_all
)
red_yellow_ratio = calculate_red_yellow_ratio(red_count, yellow_count)
red_yellow_counts.append(["Sales Count per Day", red_count, yellow_count, round(red_yellow_ratio, 2), round(avg, 2), round(std, 2)])

# Repeat for weekdays filtered
red_count, yellow_count, avg, std = plot_sales_counts_flat(
    sales_counts_weekdays_filtered,
    'Sales Count per Day (Weekdays Only)',
    'images/sales_count_weekdays_only_flat.png',
    mean_sales_weekdays_filtered,
    std_sales_weekdays_filtered
)
red_yellow_ratio = calculate_red_yellow_ratio(red_count, yellow_count)
red_yellow_counts.append(["Sales Count per Day (Weekdays Only)", red_count, yellow_count, round(red_yellow_ratio, 2), round(avg, 2), round(std, 2)])

# Repeat for TWT days
red_count, yellow_count, avg, std = plot_sales_counts_flat(
    sales_counts_twt,
    'Sales Count per Day (Tuesday, Wednesday, Thursday Only)',
    'images/sales_count_twt_only_flat.png',
    mean_sales_twt,
    std_sales_twt
)
red_yellow_ratio = calculate_red_yellow_ratio(red_count, yellow_count)
red_yellow_counts.append(["Sales Count per Day (TWT Only)", red_count, yellow_count, round(red_yellow_ratio, 2), round(avg, 2), round(std, 2)])

# Rolling plots
red_count, yellow_count, avg, std = plot_sales_counts_rolling(
    sales_counts_all,
    'Sales Count per Day With 90-Day Rolling Average',
    'images/sales_count_with_rolling_avg.png'
)
red_yellow_ratio = calculate_red_yellow_ratio(red_count, yellow_count)
red_yellow_counts.append(["Sales Count per Day With 90-Day Rolling Avg", red_count, yellow_count, round(red_yellow_ratio, 2), round(avg, 2), round(std, 2)])

# Rolling statistics for weekdays filtered
red_count, yellow_count, avg, std = plot_sales_counts_rolling(
    sales_counts_weekdays_filtered,
    'Sales Count per Day (Weekdays Only) With 90-Day Rolling Average',
    'images/sales_count_weekdays_with_rolling_avg.png'
)
red_yellow_ratio = calculate_red_yellow_ratio(red_count, yellow_count)
red_yellow_counts.append(["Sales Count per Day (Weekdays Only) With 90-Day Rolling Avg", red_count, yellow_count, round(red_yellow_ratio, 2), round(avg, 2), round(std, 2)])

# Rolling statistics for TWT days
red_count, yellow_count, avg, std = plot_sales_counts_rolling(
    sales_counts_twt,
    'Sales Count per Day (Tue, Wed, Thu) With 90-Day Rolling Average',
    'images/sales_count_twt_with_rolling_avg.png'
)
red_yellow_ratio = calculate_red_yellow_ratio(red_count, yellow_count)
red_yellow_counts.append(["Sales Count per Day (TWT With 90-Day Rolling Avg)", red_count, yellow_count, round(red_yellow_ratio, 2), round(avg, 2), round(std, 2)])

# Function to plot sales distribution with KDE
def plot_sales_distribution_with_kde(data, title, save_path):
    plt.figure(figsize=(12, 6))
    hist_bins = range(0, data['Sales Count'].max() + 10, 10)
    data['Sales Count'].hist(bins=hist_bins, density=True, alpha=0.5, color='blue', edgecolor='black')
    sns.kdeplot(data['Sales Count'], color='red', fill=True, alpha=0.3, label='KDE')

    plt.title(title, fontsize=16)
    plt.xlabel('Sales Count Bins', fontsize=14)
    plt.ylabel('Probability', fontsize=14)
    plt.legend()
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(save_path, format='png')
    plt.close()

# Plotting sales distributions for different datasets
plot_sales_distribution_with_kde(sales_counts_weekdays_filtered,
                                  'Sales Count Distribution (Weekdays Only) with KDE',
                                  'images/sales_count_weekdays_distribution_with_kde.png')

plot_sales_distribution_with_kde(sales_counts_twt,
                                  'Sales Count Distribution (Tue, Wed, Thu Only) with KDE',
                                  'images/sales_count_twt_distribution_with_kde.png')

plot_sales_distribution_with_kde(sales_counts_all,
                                  'Sales Count Distribution with KDE',
                                  'images/sales_count_distribution_with_kde.png')

# Create output directory to save the combined data
if not os.path.exists('output'):
    os.makedirs('output')

# Save combined DataFrame to CSV
combined_df.to_csv('output/combined_data.csv', index=False)

# Create summary DataFrame for red and yellow counts
summary_df = pd.DataFrame(red_yellow_counts,
                          columns=["Plot Title", "Red Bar Count", "Yellow Bar Count", "Red to Yellow Ratio (%)", "Average Sales Count", "Standard Deviation"])

# Print summary of red and yellow bar counts
print("\nSummary of Red and Yellow Bar Counts:")
print(summary_df.to_string(index=False))
