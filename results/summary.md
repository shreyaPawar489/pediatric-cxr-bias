# Results

NIH ChestX-ray14 subset: 16291 images, 5402 pediatric (1637 patients, 151 cardiomegaly). Guangzhou pediatric set (ages 1-5): 1583 normal, 4273 pneumonia.


## 1. False-positive rate on healthy images, by age (operating point 0.5)

| group         | CheXpert model      | MIMIC-CXR model     | PadChest model      |
|:--------------|:--------------------|:--------------------|:--------------------|
| Guangzhou 1-5 | 58.5% (56.1%-60.8%) | 89.4% (88.0%-90.9%) | 16.0% (14.3%-17.9%) |
| NIH 0-5       | 46.2% (40.5%-51.4%) | 93.0% (90.0%-95.8%) | 42.7% (36.4%-49.0%) |
| NIH 6-10      | 34.9% (29.3%-40.4%) | 78.5% (73.3%-82.9%) | 26.0% (21.0%-31.4%) |
| NIH 11-14     | 28.9% (22.4%-35.5%) | 66.4% (61.8%-70.4%) | 25.1% (19.1%-31.7%) |
| NIH 15-17     | 27.5% (22.8%-32.2%) | 64.2% (60.2%-68.1%) | 18.4% (14.3%-22.7%) |
| NIH 18-40     | 27.7% (25.0%-30.3%) | 59.5% (56.8%-62.0%) | 19.6% (17.3%-22.0%) |
| NIH 41-60     | 31.7% (29.7%-34.1%) | 60.1% (58.0%-62.4%) | 27.1% (24.9%-29.1%) |
| NIH 61+       | 41.3% (38.0%-45.0%) | 64.5% (61.3%-67.8%) | 32.7% (29.2%-35.9%) |


## Discrimination (NIH, all non-cardiomegaly images as negatives)

| model           | group          |   AUROC |   sensitivity |   FPR (all negatives) |   positives |     n |
|:----------------|:---------------|--------:|--------------:|----------------------:|------------:|------:|
| CheXpert model  | Children (<18) |   0.712 |         0.728 |                 0.427 |         151 |  5402 |
| CheXpert model  | Adults (18+)   |   0.682 |         0.676 |                 0.432 |        2625 | 10889 |
| PadChest model  | Children (<18) |   0.823 |         0.801 |                 0.304 |         151 |  5402 |
| PadChest model  | Adults (18+)   |   0.833 |         0.833 |                 0.335 |        2625 | 10889 |
| MIMIC-CXR model | Children (<18) |   0.670 |         0.960 |                 0.777 |         151 |  5402 |
| MIMIC-CXR model | Adults (18+)   |   0.632 |         0.882 |                 0.678 |        2625 | 10889 |


## 2. Fixes for young children (ages 0-10), mean ± sd over 10 patient-disjoint splits

Young-child pool for fixes: up to 1110 images. Test = the other half of young patients (healthy images + cardiomegaly; only 53 cardiomegaly images at ages 0-10 in total, so sensitivity is noisy). Guangzhou = external hospital, never used to build any fix. Target = adult FPR on healthy adult images.


| model           | method                            |    n | NIH 0-10 FPR   | Guangzhou FPR   | Sensitivity   |   AUROC | Adult FPR   |
|:----------------|:----------------------------------|-----:|:---------------|:----------------|:--------------|--------:|:------------|
| CheXpert model  | A. Published threshold            |    0 | 38.7% ± 2.8%   | 58.5% ± 0.0%    | 68.1% ± 8.4%  |   0.7   | 32.4%       |
| CheXpert model  | B. Pediatric threshold            |    0 | 38.7% ± 2.8%   | 58.5% ± 0.0%    | 68.1% ± 8.4%  |   0.7   | 32.4%       |
| CheXpert model  | B. Pediatric threshold            |   25 | 39.3% ± 9.4%   | 59.0% ± 10.6%   | 69.0% ± 10.7% |   0.7   | 32.4%       |
| CheXpert model  | B. Pediatric threshold            |   50 | 35.3% ± 12.3%  | 52.5% ± 17.7%   | 62.7% ± 19.9% |   0.7   | 32.4%       |
| CheXpert model  | B. Pediatric threshold            |  100 | 33.7% ± 8.6%   | 50.9% ± 10.6%   | 61.9% ± 12.0% |   0.7   | 32.4%       |
| CheXpert model  | B. Pediatric threshold            |  250 | 35.2% ± 6.3%   | 53.7% ± 5.8%    | 64.2% ± 10.5% |   0.7   | 32.4%       |
| CheXpert model  | B. Pediatric threshold            | 1110 | 33.7% ± 5.2%   | 52.1% ± 3.5%    | 63.4% ± 10.8% |   0.7   | 32.4%       |
| CheXpert model  | C. Retrained head (adults + kids) |    0 | 59.8% ± 5.0%   | 81.9% ± 3.4%    | 85.0% ± 8.4%  |   0.674 | 32.4%       |
| CheXpert model  | C. Retrained head (adults + kids) |   25 | 49.0% ± 6.3%   | 81.3% ± 3.6%    | 76.4% ± 9.2%  |   0.694 | 32.4%       |
| CheXpert model  | C. Retrained head (adults + kids) |   50 | 45.4% ± 5.1%   | 81.3% ± 3.5%    | 73.3% ± 11.1% |   0.696 | 32.4%       |
| CheXpert model  | C. Retrained head (adults + kids) |  100 | 37.6% ± 3.9%   | 80.5% ± 3.9%    | 62.5% ± 5.7%  |   0.694 | 32.4%       |
| CheXpert model  | C. Retrained head (adults + kids) |  250 | 29.0% ± 3.7%   | 79.8% ± 4.0%    | 51.3% ± 8.0%  |   0.69  | 32.4%       |
| CheXpert model  | C. Retrained head (adults + kids) | 1110 | 17.8% ± 2.3%   | 78.0% ± 4.5%    | 38.3% ± 9.3%  |   0.691 | 32.4%       |
| MIMIC-CXR model | A. Published threshold            |    0 | 83.0% ± 2.1%   | 89.4% ± 0.0%    | 95.9% ± 4.4%  |   0.672 | 60.8%       |
| MIMIC-CXR model | B. Pediatric threshold            |    0 | 83.0% ± 2.1%   | 89.4% ± 0.0%    | 95.9% ± 4.4%  |   0.672 | 60.8%       |
| MIMIC-CXR model | B. Pediatric threshold            |   25 | 61.9% ± 15.5%  | 61.9% ± 18.0%   | 79.7% ± 17.7% |   0.672 | 60.8%       |
| MIMIC-CXR model | B. Pediatric threshold            |   50 | 65.1% ± 5.4%   | 66.1% ± 5.3%    | 84.5% ± 11.7% |   0.672 | 60.8%       |
| MIMIC-CXR model | B. Pediatric threshold            |  100 | 64.3% ± 7.4%   | 65.3% ± 8.6%    | 83.1% ± 12.3% |   0.672 | 60.8%       |
| MIMIC-CXR model | B. Pediatric threshold            |  250 | 63.6% ± 7.1%   | 64.9% ± 5.4%    | 81.9% ± 13.1% |   0.672 | 60.8%       |
| MIMIC-CXR model | B. Pediatric threshold            | 1110 | 62.3% ± 5.9%   | 63.1% ± 3.3%    | 80.6% ± 14.3% |   0.672 | 60.8%       |
| MIMIC-CXR model | C. Retrained head (adults + kids) |    0 | 78.0% ± 2.9%   | 36.5% ± 9.7%    | 89.1% ± 4.2%  |   0.61  | 60.8%       |
| MIMIC-CXR model | C. Retrained head (adults + kids) |   25 | 71.4% ± 3.9%   | 36.4% ± 9.6%    | 85.5% ± 5.3%  |   0.62  | 60.8%       |
| MIMIC-CXR model | C. Retrained head (adults + kids) |   50 | 69.0% ± 3.3%   | 36.6% ± 10.8%   | 81.9% ± 7.2%  |   0.621 | 60.8%       |
| MIMIC-CXR model | C. Retrained head (adults + kids) |  100 | 62.3% ± 4.9%   | 37.4% ± 10.2%   | 79.7% ± 7.6%  |   0.612 | 60.8%       |
| MIMIC-CXR model | C. Retrained head (adults + kids) |  250 | 53.4% ± 4.7%   | 37.3% ± 10.6%   | 71.7% ± 7.9%  |   0.613 | 60.8%       |
| MIMIC-CXR model | C. Retrained head (adults + kids) | 1110 | 38.1% ± 3.5%   | 36.4% ± 10.9%   | 55.0% ± 12.6% |   0.629 | 60.8%       |
| PadChest model  | A. Published threshold            |    0 | 31.5% ± 3.5%   | 16.0% ± 0.0%    | 68.7% ± 13.0% |   0.759 | 25.5%       |
| PadChest model  | B. Pediatric threshold            |    0 | 31.5% ± 3.5%   | 16.0% ± 0.0%    | 68.7% ± 13.0% |   0.759 | 25.5%       |
| PadChest model  | B. Pediatric threshold            |   25 | 36.5% ± 12.3%  | 21.0% ± 6.9%    | 71.5% ± 21.5% |   0.759 | 25.5%       |
| PadChest model  | B. Pediatric threshold            |   50 | 31.4% ± 9.9%   | 17.1% ± 4.9%    | 64.2% ± 23.1% |   0.759 | 25.5%       |
| PadChest model  | B. Pediatric threshold            |  100 | 28.5% ± 10.2%  | 15.1% ± 4.0%    | 61.8% ± 22.0% |   0.759 | 25.5%       |
| PadChest model  | B. Pediatric threshold            |  250 | 27.5% ± 7.0%   | 14.4% ± 1.9%    | 60.5% ± 20.1% |   0.759 | 25.5%       |
| PadChest model  | B. Pediatric threshold            | 1110 | 26.5% ± 7.6%   | 14.0% ± 1.9%    | 59.4% ± 22.1% |   0.759 | 25.5%       |
| PadChest model  | C. Retrained head (adults + kids) |    0 | 59.6% ± 6.3%   | 40.4% ± 15.3%   | 92.2% ± 6.5%  |   0.703 | 25.5%       |
| PadChest model  | C. Retrained head (adults + kids) |   25 | 47.2% ± 7.9%   | 37.2% ± 13.9%   | 81.6% ± 12.1% |   0.736 | 25.5%       |
| PadChest model  | C. Retrained head (adults + kids) |   50 | 41.0% ± 6.4%   | 35.1% ± 13.0%   | 78.3% ± 12.5% |   0.745 | 25.5%       |
| PadChest model  | C. Retrained head (adults + kids) |  100 | 31.1% ± 5.9%   | 31.9% ± 11.9%   | 65.8% ± 17.5% |   0.748 | 25.5%       |
| PadChest model  | C. Retrained head (adults + kids) |  250 | 23.3% ± 4.6%   | 29.3% ± 11.5%   | 58.2% ± 22.2% |   0.747 | 25.5%       |
| PadChest model  | C. Retrained head (adults + kids) | 1110 | 14.2% ± 3.8%   | 23.0% ± 8.6%    | 40.3% ± 19.2% |   0.755 | 25.5%       |


## 3. Flagging pediatric images when age isn't documented

Linear probe on PadChest-model features, patient-disjoint 70/30 split on NIH. Child-vs-adult AUROC: 0.948. Share flagged as child by age bin: 0-5: 100%, 6-10: 98%, 11-14: 89%, 15-17: 67%, 18-40: 22%, 41-60: 5%, 61-120: 3%. External check: 40.5% of the Guangzhou images (all ages 1-5) are flagged as children.

