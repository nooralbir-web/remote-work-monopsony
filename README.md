# Remote Work and Employer Monopsony Power in Local Labor Markets

This repository contains the replication and analysis code for the project:

**"Remote Work and Employer Monopsony Power in Local Labor Markets."**

The project examines whether the expansion of remote work is associated with higher wage growth across occupations, consistent with a reduction in employer monopsony power.

The analysis combines occupation-level wage data from the U.S. Bureau of Labor Statistics (BLS) with task-level measures from the O*NET database to construct a remote-work feasibility index.

---

## Project Overview

Recent research suggests that many labor markets exhibit employer monopsony power, where firms can set wages below workers’ marginal product because workers face limited outside options.

Remote work may weaken this monopsony power by expanding workers’ employment opportunities beyond their local labor market.

This project provides preliminary empirical evidence using occupation-level variation in remote-work feasibility and wage growth between 2019 and 2023.

---

## Data Sources

The analysis combines two main datasets:

### BLS Occupational Employment and Wage Statistics (OEWS)
- Mean annual wages by occupation
- Years used: **2019 and 2023**
- Unit of observation: **6-digit SOC occupation**

Source:  
https://www.bls.gov/oes/

### O*NET Task Data
Used to construct the remote-work feasibility index.

Key task measures include:

- Physical Proximity
- Face-to-Face Discussions
- Deal With External Customers
- Performing for or Working Directly with the Public

Source:  
https://www.onetcenter.org/database.html

---

## Remote-Work Feasibility Index

The remote-work feasibility index is constructed using O*NET task measures that capture the extent to which an occupation requires physical proximity or direct interpersonal interaction.

Occupations requiring greater physical presence receive **lower remote feasibility scores**, while occupations that can be performed independently or digitally receive **higher scores**.

The index is normalized to range between **0 and 1**, where higher values represent greater feasibility of remote work.

---

## Empirical Specification

The baseline empirical model estimated in the paper is:

\[
WageGrowth_i = \alpha + \beta RemoteIndex_i + \gamma Wage2019_i + \varepsilon_i
\]

where:

- **WageGrowth** is the percent change in mean occupational wages between 2019 and 2023
- **RemoteIndex** is the O*NET-based remote-work feasibility index
- **Wage2019** controls for baseline occupational wage levels

Regressions are estimated using **OLS with heteroskedasticity-robust standard errors**.

---

## Repository Structure
