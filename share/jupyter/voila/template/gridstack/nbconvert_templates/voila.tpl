{%- extends 'base.tpl' -%}

{% block html_head_css %}
<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.2.0/css/bootstrap.min.css">
<link href="http://gridstackjs.com/dist/gridstack.css" rel="stylesheet">
{{ super() }}
<style>

.cell, .output_wrapper, .output, .output_area, .output_subarea, .widget-subarea {
    display: flex;
    flex: 1;

}
.p-Widget {
    flex: 1;
}

.grid-stack-item-content {
    background: white;
    color: #2c3e50;
    display: flex;
    flex-direction: column;
    /* font-family: 'Indie Flower', cursive; */
    /* text-align: center; */
    /* font-size: 20px; */
}

.gridhandle {
    cursor: move;
    margin-left: 10px;
}
header a, header a:hover { color: #fff; }

.darklue { background: #2c3e50; color: #fff; }
body {
    background-color: #2c3e50!important;
}
</style>
{% endblock html_head_css %}



{% block body %}

<section id="demo" class="darklue">
        <div class="container">
            <div class="row">
                <div class="col-lg-12 text-center">
                    <h2>Voila + Gridstack.js demo</h2>
                    <hr class="star-light">
                </div>
            </div>

            <div class="grid-stack" data-gs-width="12" data-gs-animate="yes">
                    {{ super() }}
                    <!-- <div class="grid-stack-item" data-gs-x="0" data-gs-y="0" data-gs-width="4" data-gs-height="2">
                    <div class="grid-stack-item-content">
                    </div> -->
            </div>
            </div>
        </div>
</section>

{% endblock body %}



{% block markdowncell scoped %}
<div class="grid-stack-item" data-gs-width="12" data-gs-height="2" data-gs-auto-position='true'>
    <div class="grid-stack-item-content">
        {{ super() }}
    </div>
</div>
{% endblock markdowncell %}

{% block codecell %}
{% if cell.metadata.grid_rows %}
<div class="grid-stack-item" data-gs-width="{{ cell.metadata.grid_columns }}" data-gs-height="{{ cell.metadata.grid_rows }}" data-gs-auto-position='true'>
    <!-- custom width/height -->
{% else %}
<div class="grid-stack-item" data-gs-width="4" data-gs-height="4" data-gs-auto-position='true'>
{% endif %}
        <div class="grid-stack-item-content">
            <div class="gridhandle">
                <i class=" fa fa-arrows"></i>
            </div>
        {{ super() }}
        </div>
</div>
{% endblock codecell %}



{% block footer_js %}

<script src="https://cdnjs.cloudflare.com/ajax/libs/jqueryui/1.12.0/jquery-ui.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jqueryui-touch-punch/0.2.3/jquery.ui.touch-punch.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/lodash.js/3.5.0/lodash.min.js"></script>


<script src="http://gridstackjs.com/dist/gridstack.js"></script>

<script src="http://gridstackjs.com/dist/gridstack.jQueryUI.js"></script>
<script type="text/javascript">
    // bqplot doesn't resize when resizing the tile, fix: fake a resize event
    var resize_workaround = _.debounce(() => {
        window.dispatchEvent(new Event('resize'));
    }, 100)
    $(function () {
        $('.grid-stack').gridstack({
            width: 12,
            alwaysShowResizeHandle: /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent),
            resizable: {
                handles: 'e, se, s, sw, w'
            },
            draggable: {
                handle: '.gridhandle',
            }
        }).on('resizestop', function(event, elem) {
            resize_workaround()
        });
    });
</script>

{{ super() }}

{% endblock footer_js %}
