// script.js
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

document.addEventListener('DOMContentLoaded', function() {
    function hideAllSections() {
        const sections = document.querySelectorAll('.section');
        sections.forEach(section => {
            section.style.display = 'none';
        });
    }
  
    document.querySelector('.nav_link.conditional').addEventListener('click', function() {
        hideAllSections();
        document.getElementById('conditionalSearchFormSection').style.display = 'block';
    });
    // ############################ Tools showing command #####################################################
    document.querySelector('.nav_link.TwoD_search').addEventListener('click', function() {
        hideAllSections();
        document.getElementById('2Dsearch').style.display = 'block';
    });
    document.querySelector('.nav_link.substructure').addEventListener('click', function() {
        hideAllSections();
        document.getElementById('substructure').style.display = 'block';
    });
    document.querySelector('.nav_link.ThreeDsearch').addEventListener('click', function() {
        hideAllSections();
        document.getElementById('ThreeDsearch').style.display = 'block';
    });
    document.querySelector('.nav_link.Maccs').addEventListener('click', function() {
        hideAllSections();
        document.getElementById('maccs').style.display = 'block';
    });
  
    // ################################### End of tools showing Command #####################################
    document.querySelector('.nav_link.Smiles').addEventListener('click', function() {
        hideAllSections();
        document.getElementById('smilesSearchSection').style.display = 'block';
    });
    document.querySelector('.nav_link.Cancer').addEventListener('click', function() {
        hideAllSections();
        document.getElementById('cancer_section').style.display = 'block';
    });
  
    document.querySelector('.nav_link.Drug_Category').addEventListener('click', function() {
        hideAllSections();
        document.getElementById('Category_section').style.display = 'block';
    });
    
  
    document.querySelector('.nav_link.Technique').addEventListener('click', function() {
        hideAllSections();
        document.getElementById('technique_section').style.display = 'block';
    });
    document.querySelector('.nav_link.basic').addEventListener('click', function() {
        hideAllSections();
        document.getElementById('searchFormSection').style.display = 'block';
    });
    
  });
  
 
  document.addEventListener("DOMContentLoaded", function() {
    document.querySelector('button[type="button"]').addEventListener("click", clearForm);
});

function clearForm() {
    var form = document.getElementById('searchForm');
    if (form) {
        form.reset();
    } else {
        console.error('Form element not found!');
    }
}
function clearSmilesForm() {
    document.getElementById('smilesSearchForm').reset();
}
function addConditionRow() {
      const tableBody = document.getElementById('conditionRows');
      const newRow = tableBody.rows[0].cloneNode(true);
      newRow.cells[0].innerText = tableBody.rows.length + 1;
      tableBody.appendChild(newRow);
  }
  
  function removeConditionRow(button) {
      const row = button.closest('tr');
      if (document.getElementById('conditionRows').rows.length > 1) {
          row.remove();
      }
  }
  function fetchDrugCategoryData(event) {
    console.log('jai');
    event.preventDefault();  // Prevent the default anchor link behavior

    fetch('/drug_category')  // Make sure this is the correct URL to your Django view
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        
        .then(data => {
            console.log(data); // This will show you what the actual data structure is.
            const tbody = document.querySelector('#peptides-table tbody');
            tbody.innerHTML = '';  // Clear existing rows
            Object.entries(data.table).forEach(([category, counts]) => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${category}</td>                     
                    <td><a href="#" data-category="${category},cell_count,Drug category" onclick="fetchData(event)">${counts.Cell_Count}</a></td>
                    <td><a href="#" data-category="${category},animal_count,Drug category" onclick="fetchData(event)">${counts.Animal_Count}</a></td>
                    <td><a href="#" data-category="${category},patient_count,Drug category" onclick="fetchData(event)">${counts.Patient_Count}</a></td>
                `;
                tbody.appendChild(row);
            });
        })
        .catch(error => console.error('Error loading the drug categories:', error));
}

function fetchtechnique(event) {
    console.log('jai');
    event.preventDefault();  // Prevent the default anchor link behavior

    fetch('/technique')  // Make sure this is the correct URL to your Django view
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        
        .then(data => {
            console.log(data); // This will show you what the actual data structure is.
            const tbody = document.querySelector('#peptidest-table tbody');
            tbody.innerHTML = '';  // Clear existing rows
            Object.entries(data.table).forEach(([category, counts]) => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${category}</td>
                    <td><a href="#" data-category="${category},cell_count,TECHNIQUE" onclick="fetchData(event)">${counts.Cell_Count}</a></td>
                    <td><a href="#" data-category="${category},animal_count,TECHNIQUE" onclick="fetchData(event)">${counts.Animal_Count}</a></td>
                    <td><a href="#" data-category="${category},patient_count,TECHNIQUE" onclick="fetchData(event)">${counts.Patient_Count}</a></td>
                `;
                tbody.appendChild(row);
            });
        })
        .catch(error => console.error('Error loading the drug categories:', error));
}

function fetchcancer(event) {
    event.preventDefault();  // Prevent the default anchor link behavior

    fetch('/cancer_type')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.log(data); // This will show you what the actual data structure is.
            const tbody = document.querySelector('#peptidestc-table tbody');
            tbody.innerHTML = '';  // Clear existing rows
            Object.entries(data.table).forEach(([category, counts]) => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${category}</td>
                    
                    <td><a href="#" data-category="${category},cell_count,Cancer_Type" onclick="fetchData(event)">${counts.Cell_Count}</a></td>
                    <td><a href="#" data-category="${category},animal_count,Cancer_Type" onclick="fetchData(event)">${counts.Animal_Count}</a></td>
                    <td><a href="#" data-category="${category},patient_count,Cancer_Type" onclick="fetchData(event)">${counts.Patient_Count}</a></td>
                `;
                tbody.appendChild(row);
            });
        })
        .catch(error => console.error('Error loading the drug categories:', error));
}


function fetchCategoryData(event) {
    event.preventDefault();
    let category = event.currentTarget.getAttribute('data-category');
    category = category.replace(/\//g, ',');
    console.log('Fetching data for category:', category);
    
    const url = '/get_category_data/' + encodeURIComponent(category) + '/';

    // Redirect to the URL which will render the new page
    window.location.href = url;
}

function fetchData(event) {
    const dataCategory = event.currentTarget.getAttribute('data-category');
    let [category, field, column] = dataCategory.split(',');

    // Replace `/` with `_SLASH_`
    category = category.replace(/\//g, ',');

    console.log('Fetching data for category:', category);
    console.log('Field:', field);
    console.log('Column:', column);
    
    const url = `/get_data/${encodeURIComponent(category)}/${encodeURIComponent(field)}/${encodeURIComponent(column)}/`;
    
    // Redirect to the URL which will render the new page
    window.location.href = url;
}

function loadColumns_search(checkbox) {
    const field = checkbox.value;
    if (checkbox.checked) {
        fetch(`/get_columns/?field=${field}`)
            .then(response => response.json())
            .then(data => {
                const columnCheckboxes = document.getElementById('column-checkboxes');
                columnCheckboxes.innerHTML = '';  // Clear previous checkboxes
                data.column_names.forEach(column => {
                    const label = document.createElement('label');
                    label.className = 'checkbox-group';
                    const input = document.createElement('input');
                    input.type = 'checkbox';
                    input.name = 'field_query';
                    input.value = column;
                    label.appendChild(input);
                    label.appendChild(document.createTextNode(` ${column}`));
                    columnCheckboxes.appendChild(label);
                });
                document.getElementById('fields-to-search').style.display = 'flex';
                document.getElementById('fields-to-search').style.flexWrap = 'wrap';
                document.getElementById('fields-to-search').style.margin = '10px 0';
            })
            .catch(error => console.error('Error loading columns:', error));
    } else {
        document.getElementById('column-checkboxes').innerHTML = '';
        document.getElementById('fields-to-search').style.display = 'none';
    }
}


function loadColumns(checkbox) {
    const field = checkbox.value;
    if (checkbox.checked) {
        fetch(`/get_columns/?field=${field}`)
            .then(response => response.json())
            .then(data => {
                const columnCheckboxes = document.getElementById('column-checkboxes');
                columnCheckboxes.innerHTML = '';  // Clear previous checkboxes
                data.column_names.forEach(column => {
                    const label = document.createElement('label');
                    label.className = 'checkbox-group';
                    const input = document.createElement('input');
                    input.type = 'checkbox';
                    input.name = 'field_query';
                    input.value = column;
                    label.appendChild(input);
                    label.appendChild(document.createTextNode(` ${column}`));
                    columnCheckboxes.appendChild(label);
                });
                document.getElementById('fields-to-search').style.display = 'flex';
                document.getElementById('fields-to-search').style.flexWrap = 'wrap';
                document.getElementById('fields-to-search').style.margin = '10px 0';
            })
            .catch(error => console.error('Error loading columns:', error));
    } else {
        document.getElementById('column-checkboxes').innerHTML = '';
        document.getElementById('fields-to-search').style.display = 'none';
    }
}

function addConditionRow() {
    const tableBody = document.getElementById('conditionRows');
    const rowCount = tableBody.rows.length + 1;
    const newRow = document.createElement('tr');
    newRow.innerHTML = `
        <td>${rowCount}</td>
        <td>
            <select name="table[]" onchange="loadColumns(this, ${rowCount})">
                <option value="all_fields">All Fields</option>
                <option value="cell_line">Cell Line</option>
                <option value="animal_studies">Animal Studies</option>
                <option value="patient_studies">Patient Studies</option>
            </select>
        </td>
        <td>
            <select name="field[]" id="field-select-${rowCount}">
                <option value="">Select Field</option>
                <!-- Options will be dynamically loaded here -->
            </select>
        </td>
        <td><input type="text" name="query[]"></td>
        <td>
            <select name="operator[]">
                <option value="and">AND</option>
                <option value="or">OR</option>
                <option value="not">NOT</option>
            </select>
        </td>
        <td><button type="button" onclick="addConditionRow()">+</button></td>
        <td><button type="button" onclick="removeConditionRow(this)">-</button></td>
    `;
    tableBody.appendChild(newRow);
}

function removeConditionRow(button) {
    const row = button.parentElement.parentElement;
    row.parentElement.removeChild(row);
}

function loadColumns(selectElement, rowIndex) {
    const fieldSelect = document.getElementById(`field-select-${rowIndex}`);
    const table = selectElement.value;

    fetch(`/get_columns/?field=${table}`)
        .then(response => response.json())
        .then(data => {
            fieldSelect.innerHTML = '';  // Clear previous options
            data.column_names.forEach(column => {
                const option = document.createElement('option');
                option.value = column;
                option.textContent = column;
                fieldSelect.appendChild(option);
            });
        })
        .catch(error => console.error('Error loading columns:', error));
}



//##################################################################Tools Javascript Code#####################################################################

// 2-D search 
document.getElementById('2D_search_form').addEventListener('submit', function(event) {
    event.preventDefault(); // Prevent form submission

    const formData = new FormData(this);
    fetch(this.action, {
        method: 'POST',
        headers: {
            'X-CSRFToken': formData.get('csrfmiddlewaretoken')
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        console.log('Response data:', data); // Debugging log
        if (data.success) {
            display2DResults(data.results);
        } else {
            // Handle error
            alert('Error fetching results:', data);
        }
    })
    .catch(error => console.error('Error:', error));
});

function display2DResults(results) {
    const searchResults = document.getElementById('searchResults2');
    const tableHeaders = document.getElementById('tableHeaders2');
    const tableBody = document.getElementById('tableBody2');

    // Clear previous results
    tableHeaders.innerHTML = '';
    tableBody.innerHTML = '';

    // Populate table headers
    if (results.length > 0) {
        console.log('Results:', results); // Debugging log
        const headers = Object.keys(results[0]);
        headers.forEach(header => {
            const th = document.createElement('th');
            th.textContent = header;
            tableHeaders.appendChild(th);
        });

        // Populate table rows
        results.forEach(row => {
            const tr = document.createElement('tr');
            headers.forEach(header => {
                const td = document.createElement('td');
                td.textContent = row[header];
                tr.appendChild(td);
            });
            tableBody.appendChild(tr);
        });
    }
    // Show the results section
    searchResults.style.display = 'block';
}

function clear2DForm() {
    document.getElementById('2D_search_form').reset();
    document.getElementById('searchResults2').style.display = 'none';
}


// 3-D search
document.getElementById('3D_search_form').addEventListener('submit', function(event) {
    event.preventDefault(); // Prevent the default form submission behavior

    // Show a confirmation dialog to the user
    const userConfirmed = confirm("This process may take some time. Do you want to proceed?");
    
    if (userConfirmed) {
        // User clicked "OK", proceed with form submission
        const formData = new FormData(this); // Create a FormData object from the form
        const loadingMessage = document.getElementById('loadingMessage');

        // Show the "It may take time" message
        loadingMessage.style.display = 'block';

        fetch(this.action, {
            method: 'POST',
            headers: {
                'X-CSRFToken': formData.get('csrfmiddlewaretoken')
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            console.log('Response data:', data); // Log response data for debugging
            loadingMessage.style.display = 'none'; // Hide the loading message

            if (data.success) {
                display3DResults(data.results); // Display the results if successful
            } else {
                // Handle error by alerting the user
                alert('Error fetching results: ' + JSON.stringify(data));
            }
        })
        .catch(error => {
            console.error('Error:', error);
            loadingMessage.style.display = 'none'; // Hide the loading message in case of error
            alert('An error occurred while fetching results.');
        });
    } else {
        // User clicked "Cancel", do nothing
        return;
    }
});

function display3DResults(results) {
    const searchResults = document.getElementById('searchResults3');
    const tableHeaders = document.getElementById('tableHeaders3');
    const tableBody = document.getElementById('tableBody3');

    // Clear previous results
    tableHeaders.innerHTML = '';
    tableBody.innerHTML = '';

    if (results.length > 0) {
        console.log('Results:', results); // Log results for debugging

        // Populate table headers based on result keys
        const headers = Object.keys(results[0]);
        headers.forEach(header => {
            const th = document.createElement('th');
            th.textContent = header;
            tableHeaders.appendChild(th);
        });

        // Populate table rows with result data
        results.forEach(row => {
            const tr = document.createElement('tr');
            headers.forEach(header => {
                const td = document.createElement('td');
                td.textContent = row[header];
                tr.appendChild(td);
            });
            tableBody.appendChild(tr);
        });

        // Show the results section
        searchResults.style.display = 'block';
    } else {
        // No results to display, hide the results section
        searchResults.style.display = 'none';
    }
}

function clear3DForm() {
    // Reset the form fields
    document.getElementById('3D_search_form').reset();

    // Hide the search results and the loading message
    document.getElementById('searchResults3').style.display = 'none';
    document.getElementById('loadingMessage').style.display = 'none';
}

//substructure 
document.getElementById('substructure_search_form').addEventListener('submit', function(event) {
    event.preventDefault(); // Prevent form submission
  
    const formData = new FormData(this);
    fetch(this.action, {
        method: 'POST',
        headers: {
            'X-CSRFToken': formData.get('csrfmiddlewaretoken')
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        console.log('Response data:', data); // Debugging log
        if (data.success) {
            displayResults(data.results);
        } else {
            // Handle error
            alert('Error fetching results:', data);
        }
    })
    .catch(error => console.error('Error:', error));
  });
  
  function displayResults(results) {
    const searchResults = document.getElementById('resultsTablesubs');
    const tableHeaders = document.getElementById('tableHeaderssubs');
    const tableBody = document.getElementById('tableBodysubs');
  
    // Clear previous results
    tableHeaders.innerHTML = '';
    tableBody.innerHTML = '';
  
    // Populate table headers
    if (results.length > 0) {
        console.log('Results:', results); // Debugging log
        const headers = Object.keys(results[0]);
        headers.forEach(header => {
            const th = document.createElement('th');
            th.textContent = header;
            tableHeaders.appendChild(th);
        });
  
        // Populate table rows
        results.forEach(row => {
            const tr = document.createElement('tr');
            headers.forEach(header => {
                const td = document.createElement('td');
                td.textContent = row[header];
                tr.appendChild(td);
            });
            tableBody.appendChild(tr);
        });
    }
    // Show the results section
    searchResults.style.display = 'block';
  }
  
  function clearSmilesForm() {
    document.getElementById('substructure_search_form').reset();
    document.getElementById('resultsTablesubs').style.display = 'none';
  }

  
// macc keys

document.getElementById('maccs_search_form').addEventListener('submit', function(event) {
    event.preventDefault(); // Prevent form submission

    const formData = new FormData(this);
    fetch(this.action, {
        method: 'POST',
        headers: {
            'X-CSRFToken': formData.get('csrfmiddlewaretoken')
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        console.log('Response data:', data); // Debugging log
        if (data.success) {
            displayMaccsResults(data.results);
        } else {
            // Handle error
            alert('Error fetching results:', data);
        }
    })
    .catch(error => console.error('Error:', error));
});

function displayMaccsResults(results) {
    const searchResults = document.getElementById('searchResultsm');
    const tableHeaders = document.getElementById('tableHeadersm');
    const tableBody = document.getElementById('tableBodym');

    // Clear previous results
    tableHeaders.innerHTML = '';
    tableBody.innerHTML = '';

    // Populate table headers
    if (results.length > 0) {
        console.log('Results:', results); // Debugging log
        const headers = Object.keys(results[0]);
        headers.forEach(header => {
            const th = document.createElement('th');
            th.textContent = header;
            tableHeaders.appendChild(th);
        });

        // Populate table rows
        results.forEach(row => {
            const tr = document.createElement('tr');
            headers.forEach(header => {
                const td = document.createElement('td');
                td.textContent = row[header];
                tr.appendChild(td);
            });
            tableBody.appendChild(tr);
        });
    }
    // Show the results section
    searchResults.style.display = 'block';
}

function clearMaccsForm() {
    document.getElementById('maccs_search_form').reset();
    document.getElementById('searchResultsm').style.display = 'none';
}
function fillExample2DForm() {
    document.getElementById('smilesInput2D').value = 'COC1=CC=CC2=C1C(=O)C1=C(O)C3=C(C[C@](O)(C[C@@H]3O[C@H]3C[C@H](N)[C@H](O)[C@H](C)O3)C(C)=O)C(O)=C1C2=O';
    document.getElementById('threshold2D').value = '0.5';
}
function fillExample3DForm() {
    document.getElementById('smilesInput3D').value = 'Cc1ccccc1';
    document.getElementById('threshold3D').value = '0.5';
}
function fillExamplemaccForm() {
    document.getElementById('smilesInputmacc').value = 'COC1=CC=CC2=C1C(=O)C1=C(O)C3=C(C[C@](O)(C[C@@H]3O[C@H]3C[C@H](N)[C@H](O)[C@H](C)O3)C(C)=O)C(O)=C1C2=O';
    document.getElementById('thresholdmacc').value = '0.5';
}
function fillExamplesubsForm() {
    document.getElementById('smilesInputsubs').value = 'COC1=CC=CC2=C1C(=O)C1=C(O)C3=C(C[C@](O)(C[C@@H]3O[C@H]3C[C@H](N)[C@H](O)[C@H](C)O3)C(C)=O)C(O)=C1C2=O';
    
}
//********************************************************************************end of tools function *****************************************************/
 
function openSection(sectionId) {
    var sections = document.querySelectorAll('.section');
    sections.forEach(section => {
        section.style.display = 'none';
    });
    document.getElementById(sectionId).style.display = 'block';
}

// Open the home section by default
function loadColumns1(element) {
    const selectedDatabase = element.value;
    fetch(`/get_columns1?field=${selectedDatabase}`, {
        method: 'GET',
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            createDynamicFields(data.columns);
        } else {
            console.error('Error fetching columns:', data.error);
        }
    })
    .catch(error => console.error('Error:', error));
}

function createDynamicFields(columns) {
    const dynamicFieldsDiv = document.getElementById('dynamic-fields');
    dynamicFieldsDiv.innerHTML = ''; // Clear previous content

    columns.forEach(column => {
        const label = document.createElement('label');
        label.setAttribute('for', column);
        label.className = 'data-submission-label';
        label.textContent = column + ':';
        
        const input = document.createElement('input');
        input.type = 'text';
        input.id = column;
        input.name = column;
        input.className = 'data-submission-input';
        
        dynamicFieldsDiv.appendChild(label);
        dynamicFieldsDiv.appendChild(input);
    });
}


function submitData() {
    // Get the selected database (cell_line, animal_studies, patient_studies)
    const selectedDatabase = document.querySelector('input[name="field"]:checked').value;

    // Collect form data
    const formData = {
        submitters_name: document.getElementById('submitters_name').value,
        email_address: document.getElementById('email_address').value,
        mailing_address: document.getElementById('mailing_address').value,
        comment: document.getElementById('comment').value,
    };

    // Add dynamic fields data (generated based on the selected database)
    const dynamicFields = document.getElementById('dynamic-fields').querySelectorAll('input');
    dynamicFields.forEach(field => {
        formData[field.name] = field.value;
    });

    // Create a new Excel workbook
    const workbook = XLSX.utils.book_new();

    // Create a sheet based on the selected database
    const worksheetData = [
        Object.keys(formData), // Header row (column names)
        Object.values(formData) // Data row (user input)
    ];
    const worksheet = XLSX.utils.aoa_to_sheet(worksheetData);

    // Append the worksheet to the workbook
    XLSX.utils.book_append_sheet(workbook, worksheet, selectedDatabase);

    // Export the Excel file
    XLSX.writeFile(workbook, 'submitted_data.xlsx');
}