# SBP - E

This is an implementation of Sandbox prefetcher, an extended variant, based on paper:

`Pugsley, Seth H., et al. "Sandbox prefetching: Safe run-time evaluation of aggressive prefetchers." 2014 IEEE 20th International Symposium on High Performance Computer Architecture (HPCA). IEEE, 2014.`

## Approach
Track recent accuracy to select the best prefetcher, it is a rule-based ensemble method.
1. read all pref trace
2. get a dataframe
3. traverse the dataframe, by window, get action(0,1,2,3)
4. from action get the address
5. output the 
   1. address file, 
   2. action partition file
  
## Run demo
`./run_demo.sh`
   
 