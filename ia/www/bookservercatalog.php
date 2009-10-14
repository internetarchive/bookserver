<? require_once '/petabox/setup.inc';

function render()
{

    $bookserver = 'http://bookserver.archive.org';
    
    # Check if running on dev host
    if (preg_match("/^www-(\w+)/", $_SERVER["SERVER_NAME"], $match)) {
        if ('mang' == $match[1]) {
            $bookserver = 'http://home.us.archive.org:12600';
        } else if ('testflip' == $match[1]) {
            $bookserver = 'http://home.us.archive.org:12601';
        }
    }
    
    Nav::bar(
         'BookServer Catalog', # title
         'texts',      # type
         'unsetXXX',   # collection
         null,         # image
         true,         # header
         null,         # bodytags
         '<link rel="stylesheet" href="' . $bookserver . '/static/catalog.css" type="text/css">', # headextra
         '');          # editable
    
    # We'd flush here so the nav can show before the rest of the page
    flush();
        
    $content = get_data($bookserver . '/index.html', $_SERVER["HTTP_USER_AGENT"], $_SERVER["HTTP_ACCEPT"]);
    echo $content;
    
    # XXX
    echo "<br/>Your accept header is: " . $_SERVER["HTTP_ACCEPT"];
    echo "<br/>Your user agent is: " . $_SERVER["HTTP_USER_AGENT"];
    
    footer();
}

/* gets the data from a URL */
/* From http://davidwalsh.name/download-urls-content-php-curl */
function get_data($url, $userAgent = null, $accept = null)
{
	$ch = curl_init();
	$timeout = 5;
	curl_setopt($ch,CURLOPT_URL,$url);
	curl_setopt($ch,CURLOPT_RETURNTRANSFER,1);
	curl_setopt($ch,CURLOPT_CONNECTTIMEOUT,$timeout);
	
	# pass through user agent and accept headers so catalog server can act appropriately
	if (!is_null($userAgent)) {
    	curl_setopt($ch, CURLOPT_USERAGENT, $userAgent);
    }
    if (!is_null($accept)) {
        curl_setopt($ch, CURLOPT_HTTPHEADER, array('Accept: ' . $accept));
    }
	
	$data = curl_exec($ch);
	curl_close($ch);
	return $data;
}

render();

?>