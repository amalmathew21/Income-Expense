const renderchart =(data,labels) => {


    const ctx = document.getElementById('myChart').getContext("2d");
  
    new Chart(ctx, {
      type: 'pie',
      data: {
        labels: labels,
        datasets: [{
          label: 'Last six month expenses',
          data: data,
          borderWidth: 1
        }]
      },
      options: {
          title:{
              display:true,
              text:'Expenses per Category'
      
            }
      }
    });
  };
  
  const getChartdata = () => {
      fetch('/expense_summary_category').then(res=>res.json()).then((results) =>
      {
          const category_data = results.expense_category_data
          const [labels,data] = [Object.keys(category_data),Object.values(category_data)]
          renderchart(data,labels)
      })
  
  }
  
  document.onload = getChartdata()
  