# Python script for domain squatting analysis (based on CSV data)
# Assumes the CSV file contains the following columns:
# 'Original Domain', 'Typo Variant', 'Squatting Type', 'Category', 'Toxic Score', 'Spam Score', 'Formality Score', 'Scraped Content'

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load data
df = pd.read_csv("../academy_results.csv")  # <- change to your actual file path

# Standardize column names
cols = ['Original Domain', 'Typo Variant', 'Squatting Type', 'Category', 'Toxic Score', 'Spam Score', 'Formality Score', 'Scraped Content']
df.columns = [c.strip() for c in df.columns if c.strip() in cols]

# Add sector labels based on domain (you need to define your own lists below)
academic_domains = [...]  # <- insert list of academic domains
cyber_domains = [...]      # <- insert list of cybersecurity domains

def label_sector(domain):
    if domain in academic_domains:
        return 'Academic'
    elif domain in cyber_domains:
        return 'Cyber'
    return 'Unknown'

df['Sector'] = df['Original Domain'].apply(label_sector)

# --- Plot 1: Category distribution of squatted domains ---
plt.figure(figsize=(12, 6))
sns.countplot(data=df, x='Category', hue='Sector', order=df['Category'].value_counts().index)
plt.xticks(rotation=45)
plt.title("Distribution of Squatted Domain Categories")
plt.tight_layout()
plt.savefig("category_distribution.png")

# --- Plot 2: Squatting techniques used ---
plt.figure(figsize=(12, 6))
sns.countplot(data=df, x='Squatting Type', hue='Sector', order=df['Squatting Type'].value_counts().index)
plt.xticks(rotation=45)
plt.title("Squatting Techniques Used")
plt.tight_layout()
plt.savefig("squatting_techniques.png")

# --- Plot 3: Share of malicious vs. neutral squats ---
def is_malicious(cat):
    return cat in ['Scam', 'Adult content', 'Affiliate abuse', 'Hit stealing']
df['Malicious'] = df['Category'].apply(lambda c: 'Malicious' if is_malicious(c) else 'Non-malicious')

plt.figure(figsize=(6, 6))
sns.histplot(data=df, x='Sector', hue='Malicious', multiple='stack', shrink=0.8, stat='percent', discrete=True)
plt.title("Share of Malicious vs. Neutral Squatted Domains")
plt.ylabel("Percent")
plt.tight_layout()
plt.savefig("malicious_ratio.png")

# --- Plot 4: Distributions of AI scores ---
fig, axes = plt.subplots(1, 3, figsize=(18, 5))
sns.histplot(df['Toxic Score'], kde=True, ax=axes[0]).set_title("Toxicity")
sns.histplot(df['Spam Score'], kde=True, ax=axes[1]).set_title("Spam")
sns.histplot(df['Formality Score'], kde=True, ax=axes[2]).set_title("Formality")
plt.tight_layout()
plt.savefig("ai_score_distributions.png")

# --- Plot 5: Heatmap of AI scores by category ---
ai_means = df.groupby('Category')[['Toxic Score', 'Spam Score', 'Formality Score']].mean()
plt.figure(figsize=(10, 6))
sns.heatmap(ai_means, annot=True, fmt=".2f", cmap="coolwarm")
plt.title("Average AI Scores per Squatted Domain Category")
plt.tight_layout()
plt.savefig("ai_vs_category_heatmap.png")

# --- Export tables ---
df.groupby(['Sector', 'Category']).size().unstack(fill_value=0).to_csv("table_category_distribution.csv")
df.groupby(['Sector', 'Squatting Type']).size().unstack(fill_value=0).to_csv("table_techniques_distribution.csv")


# --- Sample case table ---
df[['Original Domain', 'Typo Variant', 'Squatting Type', 'Category']].sample(20).to_csv("sample_squatted_domains.csv", index=False)

print("Analysis completed. Charts and tables saved.")
print(df[df['Category'] == 'Scam'][['Original Domain', 'Typo Variant']])

# --- Average number of squats per original domain ---
squats_per_domain = df.groupby('Original Domain').size().reset_index(name='Squat Count')
avg_squats = squats_per_domain['Squat Count'].mean()

# Save summary table
#squats_per_domain.to_csv("squats_per_domain.csv", index=False)

print(f"Average number of squatted domains per original domain: {avg_squats:.2f}")