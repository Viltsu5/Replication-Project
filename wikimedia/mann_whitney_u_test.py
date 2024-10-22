import pandas as pd
from scipy.stats import mannwhitneyu
import cliffs_delta
import csv

# Load the data from the CSV file
data = pd.read_csv('IST_WIK.csv')

properties = ['URL','File','Lines_of_code','Require','Ensure','Include','Attribute','Hard_coded_string','Comment','Command','File_mode','SSH_KEY']


# Split the data into defective and neutral groups
defective = data[data['defect_status'] == 1]
neutral = data[data['defect_status'] == 0]

with open('p_value_and_delta.csv', 'w', newline='', encoding='utf-8') as csvfile:    
    fieldnames = ['Property', 'P-value', 'Delta', 'Effect size interpretation']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
    writer.writeheader()
    for property in properties:
        defective_case = defective[property]
        neutral_case = neutral[property]

    # Perform the Mann-Whitney U test
        u_statistic, p_value = mannwhitneyu(defective_case, neutral_case, alternative='greater')

    # Print the results of the Mann-Whitney U test
        #print(f"Mann-Whitney U test statistic: {u_statistic}")
        print('-------------------------------------------------')
        print(f"P-value for {property}: {p_value}")

        # Calculate Cliff's Delta
        delta, res = cliffs_delta.cliffs_delta(defective_case, neutral_case)

        # Print Cliff's Delta results
        print(f"Cliff's Delta for {property}: {delta}")
        print(f"Effect size interpretation: {res}")

        #Interpret the result
        if p_value < 0.05:
            print("Reject the null hypothesis: The property count is significantly larger for defective files than neutral files.")
        else:
            print("Fail to reject the null hypothesis: The property count is not significantly different between defective and neutral files.")


        writer.writerow({'Property': property, 'P-value': p_value, 'Delta': delta, 'Effect size interpretation': res})