/**
 * Filter current packages in the page.
 * @param {String} filter 
 */
function extman_filterPackages(filter) {

    filter = filter.toUpperCase();

    // Restore category visibility
    var categories = document.getElementsByClassName('package-category');
    for (var i = 0; i<categories.length; i++) {
        cat  = categories[i];
        cat._extman_count = 0;
    }

    // Hide/Show Packages
    var packages = document.getElementsByClassName('package-item');
    for (var i = 0; i<packages.length; i++) {
        var pkg = packages[i];
        var content = pkg.textContent || pkg.innerText;
        var match = content.toUpperCase().indexOf(filter) > -1;        
        if (match) {
            pkg.style.display = '';
        }
        else {
            pkg.style.display = 'none';
        }
        var cat = pkg.closest('.package-category');       
        if (cat && match) {
            cat._extman_count = cat._extman_count+1;
        }
    }

    // Hide/Show Categories
    for (var i = 0; i<categories.length; i++) {
        cat  = categories[i];
        cat.style.display = cat._extman_count > 0 ? '' : 'none';
    }

}

/**
 * Ask for macro confirmation.
 */
function extman_confirmMacro(macro, title) {
    
    buttons = [
        ["extman_runMacro('" + macro + "')", window._TR_RUN, 'btn-danger'],
        ["extman_closeConfirmDlg()", window._TR_CLOSE, 'btn-secondary']
    ]

    extman_confirmDlg({
        title: title,
        body: '<strong>' + window._TR_CONFIRM_MACRO_RUN + '</strong><br />' + window._TR_CONFIRM_MACRO_RUN_MSG,
        buttons: buttons
    })

}

/**
 * Run Macro.
 */
function extman_runMacro(macro) {
    extman_exec('extman:///action.run_macro?macro=' + macro)
    extman_closeConfirmDlg();
}

/**
 * Replace iframe with new one to avoid security problems
 * @param url 
 * @param content 
 */
function extman_update_readme(url, content) {

    // Ensure removed previous
    $('#extmanReadmeSandbox').remove();
    
    // Create iframe   
    var frame = document.createElement('iframe');
    frame.setAttribute('id', "extmanReadmeSandbox");
    frame.setAttribute('style', "width: 100%; height: 77vh; border: none;");
    frame.setAttribute('sandbox', "allow-same-origin");

    // Disable all links
    // Hide spinner when content loaded from url into iframe
    frame.onload = function() {
        extman_frame_disable_links(frame);
        $('#readmeSpinner').hide();
    };

    // Write content directly if provided
    if (content) {
        $("#extman_ReadmeDlg .modal-body").append(frame);
        fdoc = frame.contentWindow.document;
        fdoc.open();
        fdoc.write('<html><head>')
        fdoc.write('<meta name="viewport" content="width=device-width,initial-scale=1,minimum-scale=1.0,maximum-scale=1.0,user-scalable=0,minimal-ui" />');
        fdoc.write('<link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.0/css/bootstrap.min.css" ' +
            'integrity="sha384-9aIt2nRpC12Uk9gS9baDl411NQApFmC26EwAOH8WgZl5MYYxFfc+NcPb1dKGj7Sk" crossorigin="anonymous" />')
        fdoc.write('<style>img {max-width:100% !important;}</style>')
        fdoc.write('</head><body><div class="container-fluid">')
        fdoc.write(content);
        fdoc.write('</div></body></html>')
        fdoc.close();
        extman_frame_disable_links(frame);
        $('#readmeSpinner').hide();
    }

    // Load from url if provided
    else if (url) {
        frame.src = url;
        $("#extman_ReadmeDlg .modal-body").append(frame);
    }

}


/**
 * Open a dialog with README from url.
 */
function extman_readmeDlg(link, event) {
    
    event.preventDefault();
    
    // Get info from link's data
    var self = $(link);
    var url = self.data('readme');
    var title = self.data('title') || '';
    var format = self.data('readmeformat') || 'html';

    // Prepare UI
    $('#extman_ReadmeDlg').modal('show');
    $('#extman_ReadmeDlg .pkg-title').html(title);
    $('#readmeSpinner').show();
    $('#extmanReadmeSandbox').remove();

    // Load url directly if format is html
    if (format === 'html') {
        extman_update_readme(url);
    }

    // Fetch data and parse if format is markdown or wikimedia
    else {
        fetch(url, 
            { 
                method: 'GET',
                headers: {"Accept": "*/*"}
            })
            .then(function(response) {
                if (response.status == 200) {
                    return response.text();
                }
                else {
                    extman_update_readme(null, '<div>' + window._TR_README_ERROR + '</div>');
                }
            })
            .then(function(data) {
                if (format === 'markdown') {
                    extman_update_readme(null, marked(data, {baseUrl: url, gfm: true}));
                }
                else if (format === 'mediawiki') {
                    extman_update_readme(null, wikipage(data, url));
                }
                $('#extman_ReadmeDlg').modal('handleUpdate')
            })
            .catch(function(err) {
                extman_update_readme(null, '<div>' + window._TR_README_ERROR + '</div>');
                console.log('Fetch Error: ', err);
            });    
    }
}

/**
 * Parse wikimedia's parse api result (json) into html
 * @param data 
 */
function wikipage(data, url) {
    // Parse url
    var parser = document.createElement('a');
    parser.href = url;
    // Base Url
    var baseUrl = parser.protocol + '//' + parser.host + '/';
    // Rebase urls
    console.log(data)
    data = data.replace(/(href|src)\s*=\s*(\\?['"])\s*\//ig, '$1=$2' + baseUrl)
    console.log(data)
    // Parse json
    json = JSON.parse(data);
    // Extract html
    return json.parse.text;
}