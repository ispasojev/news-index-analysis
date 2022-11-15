
#load necessary libraries
library(csv)

library(microbenchmark)

#read in data
data = read.csv("./Data/news_data.csv", sep = ";")
#read in stopwords
stopwords = read.delim("./Data/stopwords.txt", sep = "\n", skip = 3)
stopwords = stopwords[,1]
stopwords = as.vector(stopwords)



remove_stop_words = function(text) {

  # split text by whitespace
  x = unlist(strsplit(text, " "))
  # check if word is in  stopwords
  x = x[!x %in% stopwords]
  new_text = paste(x, collapse = " ")
  
  if (nchar(text) > 5) {
    return(new_text)
  }else{
    return(text)
    }
}

measure_time = function(code_chunk) {
  
  start_time = Sys.time()
  eval(code_chunk)
  Sys.sleep(1)
  end_time = Sys.time()
  
  execution_time = end_time - start_time 
  print(execution_time - 1)
}


#library(parallel)
#options(mc.cores = 2)
#sequential = {lapply(data$text, remove_stop_words)}
#multiprocessing = {mclapply(data$text, remove_stop_words)}
  


measure_time("lapply(data$text, remove_stop_words)")

library(parallel)
options(mc.cores = 4)
measure_time("mclapply(data$text, remove_stop_words)")

remove_stop_words("I am all almost ready asshole")


