###User specified:
##Initialize:
name_of_file = "super_file.txt"
input_directory = "/home/lars/playground/real/output/"
output_directory = paste(input_directory,"plots/",sep="")
sig_value = 0.05
test_type = "normal"
###---------------

setwd(input_directory)

data_frame = read.csv(name_of_file)

##Pre-diagnostics - referential values
n = dim(data_frame)[1]
m = dim(data_frame)[2]

reduced_frame = data_frame[,2:m]

if(n < 20){
  warning("Less than 20 individuals! Some tests might not work...")
}

##Diagnostics:
#(m-1) types of diagnostics, 

#1: assume that n is large and that they should follow a normal distribution (i.e. normal noise).
#1_a: multivariate normal distribution instead.
#2: assume that we have enough observations such that a non-parametric interval could be used.
#Dev: Manually choose limits to see if the code works as intended.

##Generalizable part again.
#Check which values that is desirable to use.
if(test_type == "normal"){
  ##1 - implementation:
  #Calculate mean and standard deviation.
  y_mean = apply(reduced_frame,2,mean)
  y_std = apply(reduced_frame,2,sd)
  
  #Calculate upper and lower quantile values (Confidence Interval).
  z_upper = qnorm(1-sig_value/2,mean = y_mean,sd = y_std)
  z_lower = qnorm(sig_value/2,mean = y_mean,sd =y_std)
  
  #Transferring to general case:
  upper_values = z_upper
  lower_values = z_lower
  print("Normal CI test is chosen.")
} else if(test_type == "nonparametric" & n>=20){
  ##2 - implementation:
  #Calculating empiric quantiles.
  np_upper_quant = apply(reduced_frame,2,function(x) quantile(x,1-sig_value/2))
  np_lower_quant = apply(reduced_frame,2,function(x) quantile(x,sig_value/2))
  
  #Transferring to general case:
  upper_values = np_upper_quant
  lower_values = np_lower_quant
  print("Non-parametric CI test is chosen")
} else if(test_type == "manual"){
  ##Dev: Manually choosing values to test script.
  upper_values = rep(100,m-1)
  lower_values = rep(40,m-1)
  print("Manual CI test is chosen, for testing purposes...")
} else{
  warning("Specify the type of test...")
}

#Initalize empty indexes.
index_upper = rep(0,n)
index_lower = rep(0,n)

#Loop over all SNR/CNR.
for(i in 1:(m-1)){
  
  #Get current values.
  current_comparison = reduced_frame[,i]
  current_upper = upper_values[i]
  current_lower = lower_values[i]
    
  #Intialize empty indexes.
  new_upper = rep(0,n)
  new_lower = rep(0,n)
  
  #Higher than upper:
  new_upper = (current_comparison > current_upper)
  #Lower than lower:
  new_lower = (current_comparison < current_lower)
  
  #print(i)
  #print(new_upper)
  #print(new_lower)
  
  #Merge new index with old index, using logical "OR":
  index_upper = (index_upper | new_upper)
  index_lower = (index_lower | new_lower)
}

#Merge upper and lower indices:
merge_index = (index_upper | index_lower)

if(!any(merge_index)){
  print("No outliers at all!")
  redundant_string = "No outliers at all using the test you specified."
  
  setwd(output_directory)
  write.csv(redundant_string,file = "outlier_id.txt")
  
} else {
  print("Some outliers.")
  outliers_id = data_frame[merge_index,1]
  
  out_num = length(outliers_id)
  print(out_num)
  
  #Write the IDs which has abnormal values for easier identification.
  setwd(output_directory)
  write.csv(outliers_id,file = "outlier_id.txt")
}

#Write Histograms.
library(ggplot2)

##User can change:
common_max_x = 200
common_bins = 60
##---------------

plot_gm = qplot(reduced_frame$gm_snr,geom = "histogram",
                xlab = "SNR score", ylab = "Frequency", main = "Histogram of Grey Matter SNR score",
                xlim = c(0,common_max_x),bins = common_bins) + theme_bw()
plot_wm = qplot(reduced_frame$wm_snr,geom = "histogram",
                xlab = "SNR score", ylab = "Frequency", main = "Histogram of White Matter SNR score",
                xlim = c(0,common_max_x),bins = common_bins) + theme_bw()
plot_csf = qplot(reduced_frame$csf_snr,geom = "histogram",
                 xlab = "SNR score", ylab = "Frequency", main = "Histogram of Cerebrospinal Fluid SNR score",
                 xlim = c(0,common_max_x),bins = common_bins) + theme_bw()
plot_cnr = qplot(reduced_frame$cnr,geom = "histogram",
                 xlab = "CNR score", ylab = "Frequency", main = "Histogram of CNR score",
                 xlim = c(0,common_max_x),bins = common_bins) + theme_bw()

setwd(output_directory)
ggsave(plot_gm,file = "hist_gm_snr.pdf")
ggsave(plot_wm,file = "hist_wm_snr.pdf")
ggsave(plot_csf,file = "hist_csf_snr.pdf")
ggsave(plot_cnr,file = "hist_cnr.pdf")

#Write Scatterplot.
pdf("All_ScatterPlots.pdf",width=10,height = 10)
plot(reduced_frame,xlim = c(0,common_max_x),ylim = c(0,common_max_x))
dev.off()
