const renderchart =(data,labels) => {


    const ctx = document.getElementById('myChart').getContext("2d");

    new Chart(ctx, {
      type: 'pie',
      data: {
        labels: labels,
        datasets: [{
          label: 'Last six month incomes',
          data: data,
          borderWidth: 1
        }]
      },
      options: {
          title:{
              display:true,
              text:'Incomes per Category'

            }
      }
    });
  };

  const getChartdata = () => {
      fetch('/income/income_summary_source').then(res=>res.json()).then((results) =>
      {
          const source_data = results.income_source_data
          const [labels,data] = [Object.keys(source_data),Object.values(source_data)]
          renderchart(data,labels)
      })

  }

  document.onload = getChartdata()
