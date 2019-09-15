function setinit(){
    var map = L.map('mapid').setView([35.474834, 139.367800], 14);
    return map;
};
var map = setinit();
L.tileLayer(
'https://cyberjapandata.gsi.go.jp/xyz/std/{z}/{x}/{y}.png',
{
    attribution: "<a href='https://www.gsi.go.jp/kikakuchousei/kikakuchousei40182.html' target='_blank'>国土地理院</a>|<a href='http://nlftp.mlit.go.jp/ksj/jpgis/datalist/KsjTmplt-P11.html'>国土交通省　国土数値情報</a>"
}
).addTo(map);

var l = new L.LayerGroup();
l.addLayer(geojson);
l.addTo(map)

var centercrossIcon = L.icon({
    iconUrl: '/syaro/swarm/static/crosshair.png',       
    iconSize: [35, 35], 
    iconAnchor: [17, 17],// 画像の左上が 0,0、中央下にしたければ 12,24 とする
});
var crosshair = new L.marker(map.getCenter(), {icon: centercrossIcon, clickable:false}).addTo(map); 
map.on('move', function(e) {
    crosshair.setLatLng(map.getCenter());
});
// http://tancro.e-central.tv/grandmaster/leaflet2/tutorial9.html

jQuery(function($){
    function get(args){
        var center = map.getCenter();
        args.ll = [center.lat, center.lng].join(',');
        $.ajax({
            url:'search.json',
            type:'GET',
            data:args
        })
        .done( (data) => {
            l.addLayer(L.geoJson(data.geojson));
            $('#table').html(data.table);
            $('table').attr('class', 'ui celled table');
            settable();
        })    
    };
    $('#get').click(function(){
        get({});
    });
    $('#ramen').on('click', function(){
        get({categoryId: "55a59bace4b013909087cb24"});
    });
    $('#remove_points').on('click', function(){
        l.clearLayers();
    });
    $(document).on("click", ".venue", function(){
        var t = $(this);
        t.attr('class', 'big ui loading button')
        setTimeout(function(){
            pushbutton(t);
        }, 1000);
        //$(this).parent().append($(this).val());
    });   

    function pushbutton(t){
        var args = {id: t.val()};
        $.ajax({url:'detail.json', type:'GET', data:args}).done( (data) => {
            if (data.response.venue.friendVisits){
                t.parent().children('p').html(data.response.venue.friendVisits.count);
            } else {
                t.parent().children('p').html('だれもいってないよ');
            }
        });
        t.attr('class', 'big ui disabled button')       
    };

    $('#auth').click(function(){
        setTimeout(function(){
            window.location.href = url;
        }, 1000);
    });

    var settable = function(){
        $.extend( $.fn.dataTable.defaults, { 
        language: {
            url: "https://cdn.datatables.net/plug-ins/9dcbecd42ad/i18n/Japanese.json"
        } 
        }); 
        $("table").DataTable({
            displayLength: 100,
            orderable : true,
            responsive: true,
            lengthMenu: [ 5, 10, 100, 1000],
        });
    };

});