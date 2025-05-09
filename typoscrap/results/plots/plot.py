import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load the CSV file
df = pd.read_csv("../scan_results_all.csv")

# Basic cleanup
df['Category'] = df['Category'].fillna('Uncategorized')
df['Squatting Type'] = df['Squatting Type'].fillna('unknown')

# Plot 1: Content Category Distribution
plt.figure(figsize=(10, 6))
sns.countplot(data=df, y='Category', order=df['Category'].value_counts().index)
plt.title("Distribution of Content Categories")
plt.xlabel("Number of Variants")
plt.tight_layout()
plt.savefig("category_distribution.png")
plt.clf()

# Plot 2: Squatting Technique Distribution
plt.figure(figsize=(10, 6))
sns.countplot(data=df, y='Squatting Type', order=df['Squatting Type'].value_counts().index)
plt.title("Distribution of Squatting Techniques")
plt.xlabel("Number of Variants")
plt.tight_layout()
plt.savefig("squatting_distribution.png")
plt.clf()

# Plot 3: Score Distributions (Toxicity, Spam, Formality)
score_cols = ['Toxic Score', 'Spam Score', 'Formality Score']
df[score_cols] = df[score_cols].fillna(0.0)

plt.figure(figsize=(15, 5))
for idx, score in enumerate(score_cols, 1):
    plt.subplot(1, 3, idx)
    sns.histplot(df[score], bins=20, kde=True)
    plt.title(f"{score} Distribution")
    plt.xlabel(score)
plt.tight_layout()
plt.savefig("score_distributions.png")
plt.clf()

# Optional: Print summary statistics
print("\nCategory counts:\n", df['Category'].value_counts())
print("\nSquatting types:\n", df['Squatting Type'].value_counts())
print("\nScore means:\n", df[score_cols].mean())
