
#load necessary libraries
library(csv)
library(future.apply)
library(ggplot2)

print("Number of logical cores:")
print(detectCores(logical = TRUE))
print("Number of physical cores:")
print(detectCores(logical = FALSE))


#read in data
all_data = read.csv("./Data/news_data_Experimentation.csv", sep = ";")
#read in stopwords
all_stopwords = read.delim("./Data/stopwords.txt", sep = "\n", skip = 3)
all_stopwords = all_stopwords[,1]
all_stopwords = as.vector(all_stopwords)
stopwords = all_stopwords



remove_stop_words = function(text) {
  # A simple function that first splits text via
  # whitespaces and remove then stopwords that appear in list

  # split text by whitespace
  x = unlist(strsplit(text, " "))
  # check if word is in  stopwords
  x = x[!x %in% stopwords]
  new_text = paste(x, collapse = " ")
  
  # if text is longer than 5 characters return modified text
  # else return original text
  if (nchar(new_text) > 5) {
    return(new_text)
  }else{
    return(text)
    }
}

measure_time = function(code_chunk) {
  
  start_time = Sys.time()
  eval(parse(text=code_chunk))
  end_time = Sys.time()
  
  execution_time = end_time - start_time 
  execution_time = as.numeric(execution_time, units="secs")
  print(execution_time)
}

number_of_stopwords_to_try =  c(100, 2070)
number_of_articles_to_try =  c(200, 10000, 500000)

for(n_texts in number_of_articles_to_try) {
  
  # select desired data
  data = all_data[1:n_texts,]
  
  for (n_stopwords in number_of_stopwords_to_try) {
    
    stopwords = all_stopwords[1:n_stopwords]
  
    model_name_list = c()
    execution_time_list = c()
    
    model_name_list = append(model_name_list, "Sequential")
    execution_time_list = append(execution_time_list, 
                                 measure_time("lapply(data$text, remove_stop_words)"))
    
    for (n_cores in c(2,4,8)) {
      plan(multiprocess, workers = n_workers)
      model_name_list = append(model_name_list, paste("Future ", n_cores, " Cores"))
      execution_time_list = append(execution_time_list, 
                                   measure_time("future_lapply(data$text, remove_stop_words)"))
    }
    
    visuals_df = data.frame(Model = model_name_list, 
                            Time = execution_time_list)
    
    #create a plot of the results
    results_plot = ggplot(visuals_df, aes(x = Model, y= Time))+
      geom_bar(stat="identity") +
      labs(title="Comparison of Multiprocessing Strategies in R", 
           subtitle = paste("Number of texts:", n_texts,
                           "Number of Stopwords: ", n_stopwords)) + 
      xlab("Multiprocessing Approach") +
      geom_hline(yintercept = min(execution_time_list), color ="red") +
      ylab("Execution Time in Seconds") + 
      theme_light()
    
    ggsave(paste("./data/images/Multiprocessing_Experiment_R_",
             n_texts, "_articles_",
             n_stopwords, "_stopwords.png"), 
           plot = results_plot)
    
  }

}

#library(parallel)
#options(mc.cores = 4)
#measure_time("parallel::mclapply(data$text, remove_stop_words, nc.cores=4)")



