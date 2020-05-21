/**
 * Open std confirm dialog.
 * @param { {title,body,bodySel,buttons,buttonsSel,links} } options 
 */
function extman_confirmDlg(options) {

    var title = options.title || window._TR_Confirm;
    var body = options.body || window._TR_ConfirmBody;

    var dlgTitle = $('#extman_confirmModalDlg .modal-title');
    dlgTitle.html(title);

    var bodySel = options.bodySel;
    if (bodySel) {
        body = $(bodySel).html();
    }
    var dlgBody = $('#extman_confirmModalDlg .modal-body');
    dlgBody.html(body);

    var dlgFooter = $('#extman_confirmModalDlg .modal-footer');
    if (options.buttonsSel) {
        dlgFooter.html($(options.buttonsSel).html());
    }
    else if (options.buttons) {
        var hbtns = "";
        options.buttons.forEach(function(btn) {
            // [ onclick, label, cssClass, cssStyle ] = btn
            var onclick = btn[0];
            var label = btn[1];
            var cssClass = btn.length > 2 ? btn[2] : '';
            var cssStyle = btn.length > 3 ? btn[3] : '';
            hbtns += '<button type="button" class="btn ' + cssClass 
                + '" onclick="' + onclick 
                + '" style="' + cssStyle + '">' 
                + label + '</button>';
        });
        dlgFooter.html(hbtns);
    }
    else if (options.links) {
        var hbtns = "";
        options.links.forEach(function(btn) {
            // [ href, label, cssClass, cssStyle ] = btn
            var href = btn[0];
            var label = btn[1];
            var cssClass = btn.length > 2 ? btn[2] : '';
            var cssStyle = btn.length > 3 ? btn[3] : '';
            hbtns += '<a class="btn ' + cssClass 
                + '" href="' + href 
                + '" style="' + cssStyle + '">' 
                + label + '</a>';
        });
        dlgFooter.html(hbtns);
    }

    $('#extman_confirmModalDlg').modal('show');

}

function extman_closeConfirmDlg() {
    $('#extman_confirmModalDlg').modal('hide');
}

function extman_showSpinner(modal) {
    if (modal) {
        if (modal.message) {
            $('#globalModalSpinnerText').html(modal.message);
        }
        else {
            $('#globalModalSpinnerText').html(window._TR_LOADING);
        }
        $('#globalModalSpinner').modal('show');
    }
    $('#globalSpinner').show();
}

function extman_hideSpinner() {
    $('#globalModalSpinner').modal('hide');
    $('#globalSpinner').hide();
}

/**
 * This is a workaround because qt version used in FreeCAD 0.19
 *  today (2020-05-15) does not support custom schemes in ajax calls.
 *  see: QWebEngineView 
 * @param url extman:// based url
 */
function extman_exec(url) {
    extman_showSpinner();
    script = document.createElement('iframe');
    script.style.display = 'none';
    script.defer = true;
    script.onload = function() {
        extman_hideSpinner();
        document.body.removeChild(script)
    };
    script.src = url;
    document.body.append(script);
}

/**
 * onerror handler for images with data-fallback attribute.
 * replace img.src with next fallback option.
 * 
 * attribute "data-fallback" is a list of alternative
 *   urls separated by double pipe "||"
 * 
 * @param {Element} img 
 */
function extman_onImageError(img) {
    var self = $(img);
    if (img.fallback === undefined) {
        var fallback = self.data('fallback').split('||');
        var next = fallback.shift();
        if (fallback.length > 0) {
            img.fallback = fallback;
        }
        else {
            self.off('error');
            img.fallback = false;
        }
        self.attr('src', next);
    }
    else if (Array.isArray(img.fallback)) {
        fallback = img.fallback;
        var next = fallback.shift();
        if (fallback.length > 0) {
            img.fallback = fallback;
        }
        else {
            self.off('error');
            img.fallback = false;
        }
        self.attr('src', next);
    }
    else {
        self.off('error');
        img.fallback = false;
    }
}

function extman_frame_disable_links(frame) {
    $(frame).contents().find('a').each(function() {
        $(this).attr('href', '#');
        $(this).attr('title', window._TR_DISABLED);
        $(this).attr('onclick', 'event.preventDefault()')
    });
}

/**
 * Javascript behaviour setup.
 */
$( document ).ready(function() {

    // Ajax Links
    // Catch all links with class extman-ajax and call it async.
    $('body').on('click', '.extman-ajax', function(event) {
        event.preventDefault();
        var a = $(this);
        extman_exec(a.attr('href'));
    });

    // Loading on normal links
    // Show spinner before navigation.
    $('body').on('click', '.extman-loading', function(event) {
        var message = $(this).data('spinner-message');
        var modal = { message: window._TR_LOADING };
        if (message) {
            modal = {message: message};
        }
        extman_showSpinner(modal);
    });
    
    // Remove iframe when dialog closed
    $('#extman_ReadmeDlg').on('hidden.bs.modal', function () {
        $('#extmanReadmeSandbox').remove();
    });

});

