import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('data/sorting_counts.csv')
df['Timestamp'] = pd.to_datetime(df['Timestamp'])
df.sort_values('Timestamp', inplace=True)

# Good vs Bad percentage
good = df['Red'].sum()
bad = df['Green'].sum()
reject = df['Reject'].sum()
total = good + bad + reject
percentages = [good/total*100, bad/total*100, reject/total*100]
labels = ['Good (Red)', 'Bad (Green)', 'Reject']

# Pie chart for percentages
fig1, ax1 = plt.subplots(figsize=(8, 8))
ax1.pie(percentages, labels=labels, autopct='%1.1f%%', colors=['green', 'red', 'gray'])
ax1.set_title('Good vs Bad vs Reject Percentage')
plt.show()

# Bar chart for trends
fig2, ax2 = plt.subplots(figsize=(12, 6))
df[['Red', 'Green', 'Reject']].plot(kind='bar', stacked=True, ax=ax2, color=['green', 'red', 'gray'])
ax2.set_xlabel('Timestamp')
ax2.set_ylabel('Counts')
ax2.set_title('Sorting Counts Over Time')
ax2.legend()
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# Line chart for ratios
df['Good_Bad_Ratio'] = df['Red'] / (df['Green'] + 1)  # Avoid division by zero
df['Good_Bad_Ratio'].plot(kind='line', figsize=(12, 6))
plt.xlabel('Timestamp Index')
plt.ylabel('Good/Bad Ratio')
plt.title('Good vs Bad Ratio Trend')
plt.show()