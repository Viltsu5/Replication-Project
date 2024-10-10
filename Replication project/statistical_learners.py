import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score, f1_score
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB
from sklearn.ensemble import RandomForestClassifier
from sklearn.decomposition import PCA
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import pdist
import numpy as np

# Load datasets
data = {
    "Mozilla": pd.read_csv("C:/Users/vilja/Documents/GitHub/Replication-Project/Replication project/IST_MOZ.csv"),
    "Openstack": pd.read_csv("C:/Users/vilja/Documents/GitHub/Replication-Project/Replication project/IST_OST.csv"),
    "Wikimedia": pd.read_csv("C:/Users/vilja/Documents/GitHub/Replication-Project/Replication project/IST_WIK.csv"),
    "Mirantis": pd.read_csv("C:/Users/vilja/Documents/GitHub/Replication-Project/Replication project/IST_MIR.csv")
}

# Store evaluation metrics
metrics = {
    "Mozilla": {},
    "Openstack": {},
    "Wikimedia": {},
    "Mirantis": {}
}

for dataset_name, dataset in data.items():
    # Select only the numerical columns
    numerical_data = dataset.drop("org", axis=1).drop("file_", axis=1)

    # Preprocess the data
    y = numerical_data['defect_status']
    X = numerical_data.drop('defect_status', axis=1)

    # Apply PCA to account for multi-collinearity
    pca = PCA(n_components=0.95)
    X_pca = pca.fit_transform(X)

    # Split the dataset into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X_pca, y, test_size=0.3, random_state=42)

    # Initialize the classifiers
    classifiers = {
        "CART": DecisionTreeClassifier(),
        "KNN": KNeighborsClassifier(),
        "Logistic Regression": LogisticRegression(max_iter=2000),
        "Naive Bayes": GaussianNB(),
        "Random Forest": RandomForestClassifier()
    }

    print("-" * 30)
    print(dataset_name)
    print()

    # Train and evaluate each classifier
    for name, clf in classifiers.items():
        clf.fit(X_train, y_train)
        y_pred = clf.predict(X_test)

        # Calculate evaluation metrics
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, average='binary')
        recall = recall_score(y_test, y_pred, average='binary')
        auc = roc_auc_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, average='binary')

        # Store metrics
        metrics[dataset_name][name] = {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "auc": auc,
            "f1": f1
        }

        # Print evaluation metrics
        print(f"{name} Accuracy: {accuracy:.2f}")
        print(f"{name} Precision: {precision:.2f}")
        print(f"{name} Recall: {recall:.2f}")
        print(f"{name} AUC: {auc:.2f}")
        print(f"{name} F1-Score: {f1:.2f}")
        print("-" * 30)

# Function to perform hierarcial clustering test
def hierarcial_clustering(metrics, metric_name):
    values = np.array([list(classifier_metrics[metric_name] for classifier_metrics in dataset_metrics.values()) for dataset_metrics in metrics.values()])
    clusters = fcluster(linkage(pdist(values.T, 'euclidean'), method='ward'), t=1.5, criterion='distance')
    return clusters

# Compare methods using hierarcial clustering test (simplified Scott-Knott test)
for metric_name in ["accuracy", "precision", "recall", "auc", "f1"]:
    print(f"Best methods for {metric_name}:")
    clusters = hierarcial_clustering(metrics, metric_name)
    for i, dataset_name in enumerate(metrics.keys()):
        best_method = list(metrics[dataset_name].keys())[np.argmax([metrics[dataset_name][method][metric_name] for method in metrics[dataset_name]])]
        print(f"{dataset_name}: {best_method}")
    print("-" * 30)