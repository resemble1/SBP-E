# SBP - E

Sandbox prefetcher, an extended variant
Track recent accuracy to select the best prefetcher, rule-based ensemble method

## Approach
1. read all pref trace
2. get a dataframe
3. traverse the dataframe, by window, get action(0,1,2,3)
4. from action get the address
5. output the 
   1. address file, 
   2. action partition file
  
## Run demo
`./run_demo.sh`
   
 