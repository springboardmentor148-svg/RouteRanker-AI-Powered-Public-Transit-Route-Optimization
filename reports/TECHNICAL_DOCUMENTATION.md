# RouteRanker – Technical Documentation



## 1. Project Overview



RouteRanker is an AI-powered public transit route analysis and optimization project. It uses General Transit Feed Specification (GTFS) data, Python, machine learning, and Streamlit to analyze public transportation routes and schedules.



The project studies five Indian cities:

\- Ahmedabad

\- Chennai

\- Hyderabad

\- Mumbai

\- Pune



## 2. Project Objectives



\- Process and validate GTFS datasets.

\- Analyze routes, trips, stops, and schedules.

\- Generate route-level features.

\- Identify route patterns using clustering algorithms.

\- Classify route categories using machine learning.

\- Explore hypothetical schedule optimization scenarios.

\- Display results through an interactive dashboard.



## 3. Technologies Used



| Technology | Purpose |

|---|---|

| Python | Programming language |

| Pandas | Data processing |

| NumPy | Numerical operations |

| Scikit-learn | Machine learning |

| XGBoost | Classification |

| Joblib | Model and pipeline storage |

| Matplotlib | Data visualization |

| Seaborn | Statistical visualization |

| Streamlit | Interactive dashboard |

| GTFS | Public transit schedule data |



## 4. System Architecture



The project follows this workflow:



1\. Collect GTFS datasets.

2\. Convert GTFS files into structured CSV files.

3\. Validate data and relationships.

4\. Extract route-level features.

5\. Clean and preprocess the dataset.

6\. Apply machine learning algorithms.

7\. Generate model predictions and hypothetical optimization results.

8\. Display the outputs through the Streamlit dashboard.



## 5. Module Description



### Module 1 – GTFS Conversion and Validation

\- Converts GTFS files into CSV format.

\- Validates routes, trips, stops, and stop-time relationships.

\- Checks missing values, duplicates, and invalid records.



### Module 2 – Route-Level Feature Engineering

\- Extracts route and schedule information.

\- Generates route-level indicators.

\- Examines trip counts, stop counts, and schedule characteristics.



### Module 3 – Route Data Analysis

\- Analyzes route-level features.

\- Examines schedule patterns and route relationships.

\- Generates indicators for further processing.



### Module 4 – Data Preprocessing

\- Handles missing values.

\- Removes unsuitable records.

\- Prepares numerical and categorical features.

\- Saves the preprocessing pipeline and processed datasets.



### Module 5 – Machine Learning

Clustering algorithms:

\- K-Means

\- DBSCAN



Classification algorithms:

\- Random Forest

\- XGBoost



The models identify patterns and classify route categories using the available training data.



### Module 6 – Model Inference and Route Optimization

\- Applies trained models to route data.

\- Analyzes route patterns.

\- Examines hypothetical schedule modification scenarios.

\- Compares scheduled trip counts before and after simulated changes.



### Module 7 – Interactive Dashboard and Documentation

\- Develops the Streamlit dashboard.

\- Integrates datasets, model outputs, and visualizations.

\- Provides interactive filters and downloadable results.

\- Documents the project workflow and limitations.



## 6. Machine Learning Evaluation



The classification models were evaluated using the available Chennai dataset.



| Metric | Random Forest | XGBoost |

|---|---:|---:|

| Accuracy | 99.58% | 99.58% |

| F1 Score | 99.24% | 99.25% |



These results represent performance on the available evaluation data and do not establish generalization across all five cities.



## 7. Dashboard Description



The RouteRanker dashboard contains nine pages:



1\. **Home:** Project introduction and summary.

2\. **Dataset Overview:** Displays dataset information and filters.

3\. **Exploratory Data Analysis:** Presents data patterns and visualizations.

4\. **Route Analysis:** Displays route-level information.

5\. **Clustering Results:** Presents K-Means and DBSCAN results.

6\. **Model Predictions:** Displays classification predictions.

7\. **Route Optimization:** Explores hypothetical schedule changes.

8\. **Metrics Comparison:** Compares machine learning model performance.

9\. **About:** Displays project details and information.



## 8. Installation and Execution



### Requirements

\- Python

\- pip

\- Required project datasets and model files



### Setup Commands



Run the following commands from the project directory:



```powershell

py -m venv .venv

.\\.venv\\Scripts\\Activate.ps1

py -m pip install -r requirements.txt

```



### Run the Dashboard



```powershell

py -m streamlit run dashboard/app.py

```



Open the local URL displayed in the terminal.



## 9. Project Structure



\- `dashboard/` – Streamlit dashboard application.

\- `data/` – Raw and processed datasets.

\- `models/` – Trained machine learning models.

\- `module6/` – Module 6 outputs.

\- `notebook/` – Jupyter notebooks.

\- `reports/` – Project reports and documentation.

\- `src/` – Source code.

\- `visualizations/` – Generated charts.

\- `requirements.txt` – Python dependencies.

\- `README.md` – Project overview and setup instructions.



## 10. Limitations



\- GTFS data represents planned schedules, not actual passenger counts.

\- The project does not measure real-time passenger occupancy or overcrowding.

\- Clustering results do not automatically indicate inefficient routes.

\- DBSCAN noise points are not necessarily inefficient routes.

\- Classification evaluation currently uses Chennai data.

\- Straight-line distance is not equivalent to actual road distance.

\- Optimization scenarios are hypothetical and require real-world validation.

\- A reduction in scheduled trips alone does not prove improved service quality.



## 11. Future Enhancements



\- Integrate actual passenger-count data.

\- Include road-network distances and travel times.

\- Validate optimization scenarios using operational constraints.

\- Expand model evaluation across multiple cities.

\- Improve model generalization using more representative datasets.

\- Explore real-time public transit information.



## 12. Conclusion



RouteRanker demonstrates how GTFS data analysis, machine learning, and interactive visualization can support public transit schedule analysis. It provides a structured platform for studying route patterns and exploring hypothetical schedule improvements.



**Project Title:** RouteRanker – AI-Powered Public Transit Route Analysis and Optimization
