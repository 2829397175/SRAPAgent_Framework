import numpy as np
import matplotlib.pyplot as plt

def calculate_gini(data):
    # Sort the data in ascending order
    data = np.sort(data)
    
    # Calculate the cumulative proportion of income/wealth
    cumulative_income = np.cumsum(data)
    
    # Calculate the Lorenz curve coordinates
    x = np.arange(1, len(data) + 1) / len(data)
    y = cumulative_income / np.sum(data)
    
    # Calculate the area under the Lorenz curve (A)
    area_under_curve = np.trapz(y, x)
    
    # Calculate the area under the line of perfect equality (B)
    area_perfect_equality = 0.5
    
    # Calculate the Gini coefficient
    gini_coefficient = (area_perfect_equality - area_under_curve) / area_perfect_equality
    
    return gini_coefficient, x, y

# Example data (replace with your own data)
income_data = np.array([5000, 7000, 10000, 20000, 30000, 50000, 80000, 100000, 150000, 200000])

# Calculate Gini coefficient and Lorenz curve coordinates
gini, x, y = calculate_gini(income_data)

# Plot the Lorenz curve
plt.figure(figsize=(6, 6))
plt.plot(x, y, marker='o', linestyle='-', color='b')
plt.plot([0, 1], [0, 1], linestyle='--', color='k')
plt.fill_between(x, x, y, color='lightgray')
plt.xlabel("Cumulative % of Population")
plt.ylabel("Cumulative % of Income/Wealth")
plt.title(f"Lorenz Curve (Gini Index: {gini:.2f})")
plt.grid(True)
plt.show()

print(f"Gini Index: {gini:.2f}")
