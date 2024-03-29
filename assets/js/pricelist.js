$(document).ready(function() {
  var priceListItemEditFormSelector = '#pricelist-item-edit-form',
      priceListItemAddFormSelector = '#pricelist-item-add-form',
      priceListItemEditSelector = '.pricelist-item-edit',
      $addNewProductButton = $('#add-new-pricelist-item'),
      $modalsContainer = $('#modals-container'),
      hideAddFormLinkSelector = '.hide-add-form';

  /**
   * Add new product button click - fetch and show add form
   */
  $addNewProductButton.on('click', function() {
    if ($(priceListItemAddFormSelector).length) {
      return false;
    }

    var $headerRow = $('.card-body > .pricelist-items > .header-row');

    $.get(addItemUrl, function(data) {
      $headerRow.after($(data.html));
      initUploadFields($(priceListItemAddFormSelector));
    });

    return false;
  });

  /**
   * Edit price list item link click - fetch and show modal with edit form
   */
  $(document).on('click', priceListItemEditSelector, function(e) {
    var $target = $(e.target),
        $this = $target.closest(priceListItemEditSelector),
        editUrl = $this.attr('href');

    $.get(editUrl, function(data) {
      $modalsContainer.html(data.html);
      var $priceListItemEditModal = $modalsContainer.find('#pricelist-edit-modal');

      initUploadFields($(priceListItemEditFormSelector));

      $priceListItemEditModal.modal('show');
      $priceListItemEditModal.find('.qq-thumbnail-selector').attr('src', data.image);
    });

    return false;
  });

  /**
   * Hide add pricelsit item form click- destroy form
   */
  $(document).on('click', hideAddFormLinkSelector, function() {
    $(priceListItemAddFormSelector).remove();
    return false;
  });

  /**
   * Search
   */
  var $searchInput = $('#id_query'),
      $priceListItems = $('.pricelist-items');

  /**
   * Listen to query input (search starting from 3rd letter)
   */
  $searchInput.keyup(function() {
    var query = $(this).val(),
        searchUrl = $(this).closest('#search-form').attr('action');

    var url = searchUrl + '?source=pricelist';
    if (query.length > 0) {
      url += '&q=' + query;
    }

    $searchInput.prop('disabled', true);
      $.get(url, function(data) {
        $priceListItems.html(data.html);

        $searchInput.prop('disabled', false);
        $searchInput.focus();
      });
  });

  /**
   * Edit pricelist item form submit
   */
  $(document).on('submit', priceListItemEditFormSelector, function(e) {
    var $editForm = $(this),
        url = $editForm.attr('action');

    $.post(url, $editForm.serialize(), function(data) {

      $('#pricelist-edit-modal').modal('hide');

      var $newPriceListItemRow = $(data.html);
      var $priceListItemRow = $('div[data-id="' + $newPriceListItemRow.data('id') + '"]');

      if ($priceListItemRow.length) {
        $priceListItemRow.html($(data.html).html());
      }
    })
      .fail(function(data) {
        $.each(data.responseJSON, function(k, v) {
          var $input = $('#id_' + k),
            $formGroup = $input.closest('.form-group'),
            $errorsContainer = $formGroup.closest('.form-field').find('.field-errors');

          $errorsContainer.empty();
          $.each(v, function(i, error) {
            $errorsContainer.append('<div class="field-error"><small>' + error + '</small></div>');
          });
        });
      });

    return false;
  });

  /**
   * Add pricelist item form submit
   */
  $(document).on('submit', priceListItemAddFormSelector, function(e) {
    var $editForm = $(this),
        url = $editForm.attr('action');

    $.post(url, $editForm.serialize(), function(data) {
      $(priceListItemAddFormSelector).remove();
      $('.card-body > .pricelist-items > .header-row').after($(data.html));
    })
      .fail(function(data) {
        $.each(data.responseJSON, function(k, v) {
          var $input = $('#id_' + k),
            $formGroup = $input.closest('.form-group'),
            $errorsContainer = $formGroup.closest('.form-field').find('.field-errors');

          $errorsContainer.empty();
          $.each(v, function(i, error) {
            $errorsContainer.append('<div class="field-error"><small>' + error + '</small></div>');
          });
        });
      });

    return false;
  });
});
