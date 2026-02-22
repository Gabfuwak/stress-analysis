# Components we have:

## 1 - Data extraction
- Works for all data, matches timestamps.
- Done 100%, no bug known
What we need:
- Get the questionnaire data
## 2 - Data cleaning
What we have:
- EDA peaks cleaner
- Debug view with acceleration
What we need:
- PPG data cleaning (if needed, maybe data is clean already)
## 3 - Data analysis
### 3.1 - Neurokit general extraction
- Extracts EDA in compute_basic_eda_metrics()
	mean_tonic_uS, scr_count , mean_phasic_uS, mean_scr_amp_uS, scr_peak_rate_per_min, phasic_auc_abs_uS_s
- Extracts HRV 
	hrv_meanNN, hrv_sdnn, hrv_rmssd, hrv_lf_hf

All of this is extracted into one compute_all_metrics() in a tagged dataframe like
|subject_id|condition|rep|all_metrics*

### 3.2 - Statistical analysis
- Finding trends in different situation (NE vs ES & empty vs non-empty, both at the same time) using 2-way anova
Current results:
P-values for EDA are trending but not significant (environment effects on scr_count and scr_peak_rate_per_min at p≈0.07-0.09). For HRV, especially on empty vs non-empty, it's closer to significance and would probably be good enough for a paper with a few more participants. You can check that on the last node of the ipynb



## Next steps:
- We're not looking at trends inside the signal, only the general metrics that neurokit gives. Doing it level by level, and on timestep level rather than the more general trends would probably reveal more significance.
- Cluster subjects. Some might be high or low responders and react differently to the experiments. If we can match this with the questionnaire it would be big.
- Look at accelerometer data, might find interesting stuff there too.
- Look into the under sampling problem and how we can fix it (this is in progress)
