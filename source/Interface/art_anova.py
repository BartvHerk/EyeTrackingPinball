import pandas as pd
from sklearn.preprocessing import LabelEncoder
import pingouin as pg

# Load your CSV file
df = pd.read_csv("data/stats_out/stats_conditions.csv")

# Clean column names
df.columns = df.columns.str.replace(" ", "_").str.replace("%", "pct").str.replace("#", "num")

# Encode categorical variables
for col in ["Experience", "Reflexes", "Glasses", "Session", "Ball_num", "Participant"]:
    df[col] = LabelEncoder().fit_transform(df[col])

# List of dependent variables
dependent_vars = [
    "Look_pct", "Velocity_mean", "Flipper_dist_mean", "Fixations_mean",
    "Fixations_per_second", "Saccades_mean", "Saccades_per_second",
    "Pursuits_mean", "Pursuits_per_second"
]

# Run ANOVA (factorial approximation) for each variable
for dv in dependent_vars:
    print(f"\nDependent Variable: {dv}")
    aov = pg.anova(data=df, dv=dv, between=["Experience", "Reflexes", "Glasses"], detailed=True)
    print(aov)
    
    # Interaction term manually
    df["Interaction"] = df["Experience"].astype(str) + "_" + df["Reflexes"].astype(str)
    aov_inter = pg.anova(data=df, dv=dv, between=["Interaction"], detailed=True)
    print("Interaction between Experience and Reflexes:")
    print(aov_inter)