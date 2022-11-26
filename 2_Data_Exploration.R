### Shiny app created by:

### Dario Bogenreiter


# Libraries ---------------------------------------------------------------

#for running app
library(shiny)

#interactive visuals
library(plotly)

#for data manipulation
library(tidyr)
library(dplyr)

#for raw data output
library(DT)


library("scales")


#load input data
input_data = read.csv("./data/preprocessed_and_merged_datasets.csv", sep =";")
print(names(input_data))

#defines the main layout of the web application
ui <- fluidPage(
  
  #user interface
  #set styling
  theme = shinythemes::shinytheme("lumen"),

  titlePanel(title = "News Index Analysis"),
  #h3("created by Dario Bogenreiter e11702132"), 
  
  sidebarLayout(
    
    # Sidebar with input dropdown and the table output
    sidebarPanel(
      
      selectInput("variable", choices = names(input_data), 
                  label = "Select an explainatory variable:",
                  selected = "total_number_of_articles"),
      #actionButton("raw_data", "View raw data"),
      br(),
      br(),
      DT::dataTableOutput("raw_data_table"), 
      
    ),
    
    # the center of the line graph with the index
    mainPanel(
      
      plotlyOutput("linegraph", height = "350pt")
      
    )
  ),
  
  
  
)
server <- function(input, output, session) {
  

  output$linegraph = renderPlotly({
    
    
    #print(input$variable)
    Selected_Variable = input_data[,input$variable]
    
    scaled_Selected_Variable = rescale(Selected_Variable, to=c(min(input_data$Index.Value),max(input_data$Index.Value)))
    
    coeff = 2000
    ggplot(input_data, aes(x=datetime, group=1)) +
      
      geom_line( aes(y=Index.Value), size=2, color="#4dd4b1") + 
      geom_line( aes(y=scaled_Selected_Variable ), size=2, color="#4da0d4") +
      
      scale_y_continuous(
        # Name first Axis
        name = "Index Value",
        # create a second axis and name it as well
        sec.axis = sec_axis(~./coeff, name="Scaled Explainatory Variable")
      ) + 
      
      theme(
        axis.title.y = element_text(color = "#4dd4b1", size=13),
        axis.title.y.right = element_text(color = "#4da0d4", size=13)
      ) +
      theme(axis.text.x = element_text(angle = 60, vjust = 0.5, hjust=1)) +
      
      ggtitle("Index Development & Scaled Explainatory Variable")
    
    

    #make the plot interactive
    #ggplotly(plot)
    
  })
  

  output$raw_data_table = DT::renderDataTable({
    
    #input$summary
    
  })
  
}


shinyApp(ui, server)