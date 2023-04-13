const searchField = document.querySelector("#searchField");
const tableoutput = document.querySelector('.table-output')
const maintable = document.querySelector('.app-table')
const pagination = document.querySelector('.pagination-container')
const tablebody = document.querySelector('.table-body')
tableoutput.style.display = "none"

searchField.addEventListener('keyup',(e) =>
{
    const searchValue = e.target.value;
    if(searchValue.trim().length > 0)
    {
        pagination.style.display = "none"
        tablebody.innerHTML =""
        fetch("/income/search-income", {
            body: JSON.stringify({searchText: searchValue }),
            method: "POST",
          })
            .then((res) => res.json())
            .then((data) => {
                maintable.style.display = "none"
                tableoutput.style.display = "block"

                if(data.length === 0 )
                {
                   tableoutput.innerHTML = "No results found"
     
                }
                else
                {
                    data.forEach((item) =>
                    {
                        tablebody.innerHTML += `
                        <tr>

                        <td>${item.amount}</td>
                        <td>${item.source}</td>
                        <td>${item.description}</td>
                        <td>${item.date}</td>

                        </tr> `
                   
                    }); 
                }
            
        });
    }
    else
    {
        tableoutput.style.display = "none"
        maintable.style.display = "block"
        pagination.style.display = "block"
    }
});