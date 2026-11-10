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
        document.querySelectorAll('.section').forEach(function (section) {
            section.style.display = 'none';
        });
    }

    // Sidebar links show one page section. They only exist on the home page, so a missing one (on a result page) is skipped.
    function showOnClick(linkSelector, sectionId) {
        var link = document.querySelector(linkSelector);
        if (!link) return;
        link.addEventListener('click', function () {
            hideAllSections();
            document.getElementById(sectionId).style.display = 'block';
        });
    }
    showOnClick('.nav_link.conditional', 'conditionalSearchFormSection');
    // Tools
    showOnClick('.nav_link.TwoD_search', '2Dsearch');
    showOnClick('.nav_link.substructure', 'substructure');
    showOnClick('.nav_link.ThreeDsearch', 'ThreeDsearch');
    showOnClick('.nav_link.Maccs', 'maccs');
    // Browse and search
    showOnClick('.nav_link.Smiles', 'smilesSearchSection');
    showOnClick('.nav_link.Cancer', 'cancer_section');
    showOnClick('.nav_link.Drug_Category', 'Category_section');
    showOnClick('.nav_link.Technique', 'technique_section');
    showOnClick('.nav_link.Immune', 'immune_section');
    showOnClick('.nav_link.basic', 'searchFormSection');
});

document.addEventListener("DOMContentLoaded", function () {
    var button = document.querySelector('button[type="button"]');
    if (button) button.addEventListener("click", clearForm);
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
// ---- Browse pages: drug category, technique, cancer type, immune term -----------------------------------
// One shared loader and renderer. Each count links to the studies behind it (/browse_term/), and the last rows
// of every table say how many studies the rows above leave out.
var BROWSE_PAGES = {
    drug_category: {
        url: '/drug_category/', table: '#peptides-table', noValue: 'Drug category not in the list',
        note: 'Each study has one drug category and is counted once. Studies whose category is not in the list are shown in the last row.'
    },
    technique: {
        url: '/technique/', table: '#peptidest-table', noValue: 'No technique from the list',
        note: 'A study can use several techniques and is counted under each, so the rows do not add up to the number of studies. Studies with no technique from the list are shown in the last row.'
    },
    cancer_type: {
        url: '/cancer_type/', table: '#peptidestc-table', noValue: 'Cancer type not in the list',
        note: 'A study is counted under every cancer type it lists (almost all list one). Studies whose cancer type is not in the list are shown in the last row.'
    },
    immune: {
        url: '/immune_terms/', table: '#immune-table', noValue: 'No immune term from the list',
        note: 'A study can report several immune terms and is counted under each, so the rows do not add up to the number of studies. Studies with no term from the list are shown in the last row.'
    }
};

function browseLink(kind, field, term, outcome) {
    var url = '/browse_term/?kind=' + kind + '&field=' + field + '&term=' + encodeURIComponent(term);
    return outcome && kind === 'immune' ? url + '&outcome=' + outcome : url;
}

// Footer of a Browse table: the number of studies (each counted once), those the rows above leave out, and a note
function appendBrowseTotals(tbody, data, page) {
    if (!data.totals) return;
    var rows = [
        ['Total studies (each counted once)', data.totals, true],
        [page.noValue, data.unassigned, false]
    ];
    rows.forEach(function (spec) {
        var row = document.createElement('tr');
        row.className = 'browse-total';
        var label = document.createElement('td');
        label.textContent = spec[0];
        if (spec[2]) label.style.fontWeight = '600';
        row.appendChild(label);
        ['Cell_Count', 'Animal_Count', 'Patient_Count'].forEach(function (key) {
            var cell = document.createElement('td');
            cell.textContent = spec[1][key];
            if (spec[2]) cell.style.fontWeight = '600';
            row.appendChild(cell);
        });
        tbody.appendChild(row);
    });
    var table = tbody.closest('table');
    var note = table.nextElementSibling;
    if (!note || !note.classList.contains('browse-note')) {
        note = document.createElement('p');
        note.className = 'browse-note';
        table.insertAdjacentElement('afterend', note);
    }
    var text = page.note;
    if (data.mentions) {
        text += ' ' + Math.round(100 * data.listed / data.mentions) + '% of the terms in the data are in this list; the rest are spelling variants or not yet standardised.';
    }
    note.textContent = text;
}

function renderBrowse(kind, data) {
    var page = BROWSE_PAGES[kind];
    var tbody = document.querySelector(page.table + ' tbody');
    tbody.innerHTML = '';
    var outcome = kind === 'immune' ? document.getElementById('immune-outcome').value : null;
    var table = tbody.closest('table');
    var message = table.previousElementSibling;
    if (message && message.classList.contains('browse-message')) message.remove();
    if (data.missing) {
        message = document.createElement('p');
        message.className = 'browse-message browse-note';
        message.textContent = 'These terms are not in the database yet. They appear once the updated data has been imported.';
        table.insertAdjacentElement('beforebegin', message);
        return;
    }
    Object.keys(data.table).forEach(function (name) {
        var counts = data.table[name];
        var row = document.createElement('tr');
        var label = document.createElement('td');
        label.textContent = name;
        row.appendChild(label);
        [['Cell_Count', 'cell_count'], ['Animal_Count', 'animal_count'], ['Patient_Count', 'patient_count']].forEach(function (pair) {
            var cell = document.createElement('td');
            if (counts[pair[0]] > 0) {
                var link = document.createElement('a');
                link.href = browseLink(kind, pair[1], name, outcome);
                link.textContent = counts[pair[0]];
                cell.appendChild(link);
            } else {
                cell.textContent = counts[pair[0]];
            }
            row.appendChild(cell);
        });
        tbody.appendChild(row);
    });
    appendBrowseTotals(tbody, data, page);
}

function loadBrowse(kind, event) {
    if (event) event.preventDefault();
    var url = BROWSE_PAGES[kind].url;
    if (kind === 'immune') url += '?outcome=' + encodeURIComponent(document.getElementById('immune-outcome').value);
    fetch(url)
        .then(function (response) {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(function (data) { renderBrowse(kind, data); })
        .catch(function (error) { console.error('Error loading the ' + kind + ' counts:', error); });
}

function fetchDrugCategoryData(event) { loadBrowse('drug_category', event); }
function fetchtechnique(event) { loadBrowse('technique', event); }
function fetchcancer(event) { loadBrowse('cancer_type', event); }
function fetchImmune(event) { loadBrowse('immune', event); }


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
                <option value="cell_line" selected>Cell Line</option>
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
    loadColumns(newRow.querySelector('select[name="table[]"]'), rowCount);  // preselected database -> fields ready
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
            updateConditionHelp(fieldSelect);
        })
        .catch(error => console.error('Error loading columns:', error));
}



//##################################################################Tools Javascript Code#####################################################################
// This file is loaded twice on the home page (head and end of body), so top-level state uses `var`
// and the form wiring below is guarded to run only once.

// Suggestions offered under the SMILES boxes. Every drug listed here has entries in the database.
var TOOL_DRUG_EXAMPLES = [
    {name: 'Daunorubicin', smiles: 'COC1=CC=CC2=C1C(=O)C1=C(O)C3=C(C[C@](O)(C[C@@H]3O[C@H]3C[C@H](N)[C@H](O)[C@H](C)O3)C(C)=O)C(O)=C1C2=O'},
    {name: 'Gemcitabine', smiles: 'NC1=NC(=O)N(C=C1)[C@@H]1O[C@H](CO)[C@@H](O)C1(F)F'},
    {name: 'Lenalidomide', smiles: 'NC1=CC=CC2=C1CN(C1CCC(=O)NC1=O)C2=O'},
    {name: 'Decitabine', smiles: 'NC1=NC(=O)N(C=N1)[C@H]1C[C@H](O)[C@@H](CO)O1'},
    {name: 'Imatinib', smiles: 'CN1CCN(CC2=CC=C(C=C2)C(=O)NC2=CC(NC3=NC=CC(=N3)C3=CN=CC=C3)=C(C)C=C2)CC1'},
    {name: 'Cyclophosphamide', smiles: 'ClCCN(CCCl)P1(=O)NCCCO1'},
    {name: 'Sorafenib', smiles: 'CNC(=O)C1=NC=CC(OC2=CC=C(NC(=O)NC3=CC(=C(Cl)C=C3)C(F)(F)F)C=C2)=C1'}
];
// Substructure search takes a fragment rather than a whole drug.
var TOOL_FRAGMENT_EXAMPLES = [
    {name: 'Glutarimide ring', smiles: 'O=C1CCCC(=O)N1'},
    {name: 'Benzene ring', smiles: 'c1ccccc1'},
    {name: 'Pyrimidine ring', smiles: 'c1cncnc1'},
    {name: 'Indole', smiles: 'c1ccc2[nH]ccc2c1'}
];

// One entry per tool form: where its results go, and the defaults used by its Example button.
var TOOL_FORMS = {
    '2D_search_form': {
        results: 'searchResults2', headers: 'tableHeaders2', body: 'tableBody2', info: 'toolInfo2D',
        smiles: 'smilesInput2D', threshold: 'threshold2D', defaultThreshold: '0.5', examples: TOOL_DRUG_EXAMPLES
    },
    '3D_search_form': {
        results: 'searchResults3', headers: 'tableHeaders3', body: 'tableBody3', info: 'toolInfo3D',
        smiles: 'smilesInput3D', threshold: 'threshold3D', defaultThreshold: '0.5', examples: TOOL_DRUG_EXAMPLES,
        loading: 'loadingMessage', confirm: 'This process may take some time. Do you want to proceed?'
    },
    'substructure_search_form': {
        results: 'resultsTablesubs', headers: 'tableHeaderssubs', body: 'tableBodysubs', info: 'toolInfoSubs',
        smiles: 'smilesInputsubs', examples: TOOL_FRAGMENT_EXAMPLES
    },
    'maccs_search_form': {
        results: 'searchResultsm', headers: 'tableHeadersm', body: 'tableBodym', info: 'toolInfoMaccs',
        smiles: 'smilesInputmacc', threshold: 'thresholdmacc', defaultThreshold: '0.5', examples: TOOL_DRUG_EXAMPLES
    }
};

function formatToolValue(value) {
    if (value === null || value === undefined || value === '') return 'N/A';
    if (typeof value === 'number' && !Number.isInteger(value)) return value.toFixed(3);
    return String(value);
}

// "27 matches · searched 1019 of 1379 entries (360 without a usable structure were skipped) · method · ..."
function toolSummary(info) {
    if (!info) return '';
    var searched = 'searched ' + info.entries_searched + ' of ' + info.entries_total + ' entries';
    var skipped = info.entries_total - info.entries_searched;
    if (skipped > 0) searched += ' (' + skipped + ' without a usable structure skipped)';
    var parts = [info.matches + (info.matches === 1 ? ' match' : ' matches'), searched, info.method];
    if (info.threshold !== undefined) parts.push('threshold ' + info.threshold);
    if (info.software) parts.push(info.software);
    return parts.join(' · ');
}

function renderToolResults(cfg, data) {
    var results = data.results || [];
    var headers = results.length ? (data.columns && data.columns.length ? data.columns : Object.keys(results[0])) : [];
    var tableHeaders = document.getElementById(cfg.headers);
    var tableBody = document.getElementById(cfg.body);
    var info = document.getElementById(cfg.info);

    tableHeaders.innerHTML = '';
    tableBody.innerHTML = '';

    headers.forEach(function (header) {
        var th = document.createElement('th');
        th.textContent = header.replace(/_/g, ' ');
        tableHeaders.appendChild(th);
    });
    results.forEach(function (row) {
        var tr = document.createElement('tr');
        headers.forEach(function (header) {
            var td = document.createElement('td');
            td.textContent = formatToolValue(row[header]);
            if (header === 'STR_LINK_(SMILES)') td.className = 'smiles-cell';
            tr.appendChild(td);
        });
        tableBody.appendChild(tr);
    });

    if (info) {
        info.textContent = toolSummary(data.info);
        if (!results.length) {
            info.textContent += (info.textContent ? ' — ' : '') +
                'No entries matched. Try a lower threshold, a different study type, or one of the suggested examples.';
        }
    }
    document.getElementById(cfg.results).style.display = 'block';
}

function initToolForm(formId) {
    var cfg = TOOL_FORMS[formId];
    var form = document.getElementById(formId);
    if (!form) return;

    form.addEventListener('submit', function (event) {
        event.preventDefault();
        if (cfg.confirm && !confirm(cfg.confirm)) return;

        var formData = new FormData(form);
        var loading = cfg.loading && document.getElementById(cfg.loading);
        var submit = form.querySelector('button[type="submit"]');
        if (loading) loading.style.display = 'block';
        if (submit) submit.disabled = true;  // a second click would start a second search

        fetch(form.action, {
            method: 'POST',
            headers: {'X-CSRFToken': formData.get('csrfmiddlewaretoken')},
            body: formData
        })
        .then(function (response) { return response.json(); })
        .then(function (data) {
            if (data.success) {
                renderToolResults(cfg, data);
            } else {
                alert('Error fetching results: ' + (data.error || 'unknown error'));
            }
        })
        .catch(function (error) {
            console.error('Error:', error);
            alert('An error occurred while fetching results.');
        })
        .then(function () {
            if (loading) loading.style.display = 'none';
            if (submit) submit.disabled = false;
        });
    });
}

// Typeahead list plus clickable "Try:" chips under the SMILES box
function initToolExamples(formId) {
    var cfg = TOOL_FORMS[formId];
    var input = document.getElementById(cfg.smiles);
    if (!input) return;

    var list = document.createElement('datalist');
    list.id = cfg.smiles + 'Suggestions';
    var chips = document.createElement('div');
    chips.className = 'example-chips';
    var label = document.createElement('span');
    label.className = 'chips-label';
    label.textContent = 'Try:';
    chips.appendChild(label);

    cfg.examples.forEach(function (example) {
        var option = document.createElement('option');
        option.value = example.smiles;
        option.label = example.name;
        list.appendChild(option);

        var chip = document.createElement('button');
        chip.type = 'button';
        chip.className = 'example-chip';
        chip.textContent = example.name;
        chip.title = example.smiles;
        chip.addEventListener('click', function () { input.value = example.smiles; });
        chips.appendChild(chip);
    });

    input.setAttribute('list', list.id);
    input.setAttribute('autocomplete', 'off');
    input.parentNode.insertBefore(list, input.nextSibling);
    input.parentNode.insertBefore(chips, list.nextSibling);
}

// Example buttons: first suggestion plus the tool's default threshold
function fillToolExample(formId) {
    var cfg = TOOL_FORMS[formId];
    document.getElementById(cfg.smiles).value = cfg.examples[0].smiles;
    if (cfg.threshold) document.getElementById(cfg.threshold).value = cfg.defaultThreshold;
}
function fillExample2DForm() { fillToolExample('2D_search_form'); }
function fillExample3DForm() { fillToolExample('3D_search_form'); }
function fillExamplemaccForm() { fillToolExample('maccs_search_form'); }
function fillExamplesubsForm() { fillToolExample('substructure_search_form'); }

function clearToolForm(formId) {
    var cfg = TOOL_FORMS[formId];
    document.getElementById(formId).reset();  // restores the default threshold and study type
    document.getElementById(cfg.results).style.display = 'none';
    var loading = cfg.loading && document.getElementById(cfg.loading);
    if (loading) loading.style.display = 'none';
}
function clear2DForm() { clearToolForm('2D_search_form'); }
function clear3DForm() { clearToolForm('3D_search_form'); }
function clearSubstructureForm() { clearToolForm('substructure_search_form'); }
function clearMaccsForm() { clearToolForm('maccs_search_form'); }

document.addEventListener('DOMContentLoaded', function () {
    if (window.__toolFormsReady) return;
    window.__toolFormsReady = true;
    Object.keys(TOOL_FORMS).forEach(function (formId) {
        initToolForm(formId);
        initToolExamples(formId);
    });
});
//********************************************************************************end of tools function *****************************************************/
 
// Shows one page section. Subsections of Information (FAQs, Architecture, Download & API ...) live inside
// #information, so opening one has to open that parent as well, or it stays hidden.
function openSection(sectionId) {
    var target = document.getElementById(sectionId);
    if (!target) return;
    document.querySelectorAll('.section').forEach(function (section) {
        section.style.display = 'none';
    });
    if (target.classList.contains('information-subsection')) {
        showSubsection(sectionId);
    } else {
        target.style.display = 'block';
    }
}

function showSubsection(subsectionId) {
    var info = document.getElementById('information');
    var subsection = document.getElementById(subsectionId);
    if (!info || !subsection) return;
    info.style.display = 'block';
    document.querySelectorAll('.information-subsection').forEach(function (section) {
        section.style.display = 'none';
    });
    subsection.style.display = 'block';
}

// Entry counts in the Download & API table come from the status endpoint
function loadApiCounts() {
    var cells = document.querySelectorAll('.api-count');
    if (!cells.length) return;
    fetch('/api/v1/status/')
        .then(function (response) { return response.json(); })
        .then(function (data) {
            if (!data.studies) return;
            cells.forEach(function (cell) {
                var count = cell.dataset.study === 'all' ? data.total : data.studies[cell.dataset.study];
                if (count !== undefined) cell.textContent = count.toLocaleString();
            });
        })
        .catch(function () { /* the table is still useful without counts */ });
}
document.addEventListener('DOMContentLoaded', loadApiCounts);

// Galleries (home page figures, Help page): a list of descriptions on the left, the clicked image on the right.
// Nothing changes by itself; the first item is shown until another one is clicked.
// A gallery can name a heading and a text (data-heading-target, data-text-target) that follow the chosen figure:
// an item with data-heading / data-text replaces them, an item without brings back what the page was loaded with.
function initGalleries() {
    if (window.__galleriesReady) return;
    window.__galleriesReady = true;
    document.querySelectorAll('[data-gallery]').forEach(function (gallery) {
        var image = gallery.querySelector('.gallery-view img');
        var items = gallery.querySelectorAll('.gallery-item');
        var heading = gallery.dataset.headingTarget ? document.querySelector(gallery.dataset.headingTarget) : null;
        var text = gallery.dataset.textTarget ? document.querySelector(gallery.dataset.textTarget) : null;
        var original = {heading: heading ? heading.textContent : '', text: text ? text.textContent : ''};
        items.forEach(function (item) {
            item.addEventListener('click', function () {
                items.forEach(function (other) {
                    other.classList.toggle('active', other === item);
                    other.setAttribute('aria-pressed', other === item ? 'true' : 'false');
                });
                image.src = item.dataset.src;
                image.alt = item.dataset.alt || '';
                if (heading) heading.textContent = item.dataset.heading || original.heading;
                if (text) text.textContent = item.dataset.text || original.text;
            });
        });
    });
}
document.addEventListener('DOMContentLoaded', initGalleries);

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
        const help = fieldHelp(column);

        const label = document.createElement('label');
        label.setAttribute('for', column);
        label.className = 'data-submission-label';
        label.textContent = column + ':';
        if (help) label.appendChild(makeHelpTip(help.text, help.example));

        const input = document.createElement('input');
        input.type = 'text';
        input.id = column;
        input.name = column;
        input.className = 'data-submission-input';
        if (help) input.placeholder = 'e.g. ' + help.example;

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

// ---------------------------------------------------------------------------------------------
// Field help: one description and one example per database field, used by every form that shows
// fields (Basic search, Conditional search, Data Submission). Examples are real values from the
// database. Fields are matched on a normalised name (lower case, letters and digits only), so
// 'KEGG DRUG ID' and 'KEGG_Drug__ID' are the same field.
// ---------------------------------------------------------------------------------------------
var FIELD_HELP = [
    {key: /^id$/, text: 'Unique identifier of the entry in the database.', example: 'CANIMM/1054'},
    {key: /^drug$/, text: 'Name of the drug as given in the research article.', example: 'Gemcitabine'},
    {key: /^drugcategory$/, text: 'Class of drugs the drug belongs to.', example: 'Nucleoside Analogue'},
    {key: /^drugbankid$/, text: 'Identifier of the drug in DrugBank.', example: 'DB00441'},
    {key: /^targetsormechanismofaction$/, text: 'Target(s) or mechanism of action of the drug.', example: 'Inhibition of DNA polymerase'},
    {key: /^keggdrugid$/, text: 'Identifier of the drug in KEGG.', example: 'D02368'},
    {key: /^(drugpubchem|pubchemid|pubchem)$/, text: 'Identifier of the drug in PubChem.', example: '60750'},
    {key: /^strlinksmiles$/, text: 'Chemical structure of the drug as a SMILES string (a text notation for molecules).', example: 'NC1=NC(=O)N(C=C1)[C@@H]1O[C@H](CO)[C@@H](O)C1(F)F'},
    {key: /^singlecombination$/, text: 'Whether the drug was given alone or together with other drugs.', example: 'Single Drug'},
    {key: /^pmid$/, text: 'PubMed ID of the article the information was curated from.', example: '27687804'},
    {key: /^cancertype$/, text: 'Cancer studied in the article.', example: 'Pancreas Cancer'},
    {key: /^cancertypedescription$/, text: 'More specific description of the cancer or tissue studied.', example: 'Pancreatic Adenocarcinoma'},
    {key: /^(system|celllinesystem)$/, text: 'Cell line (or expression system) the experiment was performed on.', example: 'HCT116'},
    {key: /^dose$/, text: 'Dose or concentration of the drug with its units, as reported in the article. Units differ between study types, for example µM for cell lines and mg/kg for animals.', example: '1 µM'},
    {key: /^technique$/, text: 'Assay used to study the effect of the drug.', example: 'Flow cytometry'},
    {key: /^negativeimmune/, text: 'Immune components whose number or function increased after drug treatment and resulted in decreased anticancer immunity.', example: 'PD-L1 levels'},
    {key: /^immune.*enhanced/, text: 'Immune components whose number or function increased after drug treatment and resulted in increased anticancer immunity.', example: 'effector T cells'},
    {key: /^immune.*inhibited/, text: 'Immune components whose number or function decreased after drug treatment and resulted in decreased anticancer immunity.', example: 'Treg'},
    {key: /^immune.*unaffected/, text: 'Immune components whose number or function was not changed by the drug treatment.', example: 'TNFα expression and secretion by the macrophages'},
    {key: /^controlledtechnique$/, text: 'The assay, written with a standardised name. Several names are separated by semicolons.', example: 'Flow cytometry'},
    {key: /^controlledterms.*enhanced/, text: 'Standardised immune terms for what increased after drug treatment and resulted in increased anticancer immunity. Several terms are separated by semicolons.', example: 'NK cells; T cells'},
    {key: /^controlledterms.*inhibited/, text: 'Standardised immune terms for what decreased after drug treatment and resulted in decreased anticancer immunity. Several terms are separated by semicolons.', example: 'Regulatory T cells (Tregs)'},
    {key: /^controlledterms.*unaffected/, text: 'Standardised immune terms for what was not changed by the drug treatment. Several terms are separated by semicolons.', example: 'NK cells; CD8+ T cells; T cells'},
    {key: /^controlledterms.*negative/, text: 'Standardised immune terms for what increased after drug treatment and resulted in decreased anticancer immunity. Several terms are separated by semicolons.', example: 'PD-L1 / CD274'},
    {key: /^animalstrain/, text: 'Strain of the animal in which the anticancer activity was tested in vivo.', example: 'BALB/c'},
    {key: /^celllineusedtoinducetumor/, text: 'Cell line used to induce the tumor in the animals.', example: 'CT26 cells'},
    {key: /^patientsample/, text: 'Number of patient samples the study was carried out on.', example: '10 patients'},
    {key: /^malefemale$/, text: 'Number of male and female patients.', example: '8M/9F'},
    {key: /^medianage/, text: 'Median age or age range of the patients.', example: '62 (range 33–82)'},
    {key: /^(tertiaryremark|comment|unnamed\d*)$/, text: 'Additional notes from the curators on the study.', example: 'T cell infiltration occurred in all patients early after treatment initiation'}
];

function fieldKey(name) {
    return String(name).toLowerCase().replace(/[^a-z0-9]/g, '');
}

function fieldHelp(name) {
    var key = fieldKey(name);
    for (var i = 0; i < FIELD_HELP.length; i++) {
        if (FIELD_HELP[i].key.test(key)) return FIELD_HELP[i];
    }
    return null;
}

// The "?" icon used on every form; the text shows on hover or keyboard focus (see .help-tip in index.css)
function makeHelpTip(text, example) {
    var tip = document.createElement('span');
    var full = text + (example ? ' Example: ' + example + '.' : '');
    tip.className = 'help-tip';
    tip.tabIndex = 0;
    tip.setAttribute('role', 'img');
    tip.setAttribute('aria-label', full);
    tip.dataset.tip = full;
    tip.textContent = '?';
    return tip;
}

// Conditional search: the Field drop-down gets a tip (and the Query box a placeholder) for the chosen field
function updateConditionHelp(fieldSelect) {
    var row = fieldSelect.closest('tr');
    if (!row) return;
    var help = fieldHelp(fieldSelect.value);
    var cell = fieldSelect.parentNode;
    var old = cell.querySelector('.help-tip');
    if (old) old.remove();
    if (help) cell.appendChild(makeHelpTip(help.text, help.example));
    var query = row.querySelector('input[name="query[]"]');
    if (query) query.placeholder = help ? 'e.g. ' + help.example : '';
}
document.addEventListener('change', function (event) {
    if (event.target.matches && event.target.matches('#conditionRows select[name="field[]"]')) {
        updateConditionHelp(event.target);
    }
});
document.addEventListener('DOMContentLoaded', function () {
    // fill the first row's Field list for the preselected database, so the form works without any clicks
    var first = document.querySelector('#conditionRows select[name="table[]"]');
    if (first) loadColumns(first, 1);
});
