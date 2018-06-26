import urllib.parse
import xml.etree.ElementTree as ET
import aiohttp
from aiohttp import web
import aiohttp_jinja2
import jinja2

searchapp_routes = web.RouteTableDef()
searchapp = web.Application()
aiohttp_jinja2.setup(searchapp,
    loader=jinja2.FileSystemLoader('.'))


# TODO I could try to make this its own web page, use the html format
# TODO is that useful?

@searchapp_routes.view('', name='search')
class Search(web.View):
    """
    Query the info on the images available
    Methods: GET

    query:
        To search via query string, add `?query=<query>` where `<query>` is
        a comma separated list of package names or a name followed by a version
        in the format `name=version`
        
        For example, `query=vim,python3,wget=7,apt`
        
        Names and versions are fuzzy matched, meaning they will match against
        any package that contains the query term

    format:
        To select the format, add `&format=<format>` where `<format>` can be
        `json` or `xml`

        We also check the `Accept` header for `application/json` or
        `application/xml`
    """
    @classmethod
    def gen_docstring(cls):
        return cls.__doc__

    async def get(self):
        """
        Get some text
        """
        request = self.request
        query_string = request.query_string
        app = request.app
        #info_dict = app['info_dict']
        #print(query_string)
        qs = urllib.parse.parse_qs(query_string)
        #print(qs)
        # Get the desired format. Default is json
        format = None
        # First priority is anything in the query_string
        if 'format' in qs:
            format = qs['format'][0]
        # Next, we check the Accept header for mime types
        elif 'ACCEPT' in request.headers:
            # TODO this uses pythons lack of namespace in for loops, may want to do this another way if they fix that
            for accept in request.headers.getall('ACCEPT', []):
                #print('accapt:', accept)
                for mimetype in accept.split(','):
                    #print('mimetype:', mimetype, len(mimetype), len(mimetype.strip()))
                    # TODO do I want to include the other html MIME types?
                    if mimetype == 'text/html':
                        format = 'html'
                        break
                    elif mimetype == 'application/json':
                        format = 'json'
                        break
                    elif mimetype == 'application/xml':
                        format = 'xml'
                        break
                if format is not None:
                    # We really need a "if we broke out" clause for the for loop
                    break
            else:
                format = 'json'
        # Finally, we default to json
        else:
            format = 'json'
        #print('format:', format)
        
        # Next, we get the search query
        # Fist is the query string
        if 'query' in qs:
            query = qs['query'][0]
        # Next, we check the body for json data
        # TODO this is actually more for POST, but we aren't implementing post
        elif request.content_type == 'application/json':
            if not request.can_read_body:
                print("Got JSON but couldn't read it")
            query = await request.json()['query']
        else:
            query = ''
        #print('query: ', query)
        _help = True if 'help' in query else False  # TODO print docstring if ?help
        
        # Terms are query criteria as (package name, version)
        terms = [(term.split('=')[0], '' if len(term.split('=')) == 1 else term.split('=')[1]) for term in query.split(',') if query]
        #print(terms)
        
        # Perform the search
        images = request.config_dict['images']  # config_dict searches through the partent modules until it hits the first match; its how we get stuff on the root app
        term_results = {}
        
        for image_name, info in images.items():
            for package_name, package_version in terms:
                result = await info.async_search(package_name, version=package_version)
                if not result:
                    try:
                        del term_results[image_name]
                    except:
                        pass
                    break
                try:
                    term_results[image_name].append(result)
                except KeyError:
                    term_results[image_name] = [result]
        
        #print(term_results)
        # XXX We don't include duplicate names when making the search dict, so we don't need to think about it here
        # TODO I'd like this to be ordered somehow, smallest image_names first because they are more likely to be the most relevant
        # TODO but I know dicts are unordered, perhaps transform it into an ordered dict?
        results = {image_name: {app['name']: app for term in term_results[image_name] for app in term} for image_name in term_results}
        
        response = {'results': results, 'query': query}
        if format == 'json':
            return web.json_response(response)
        elif format == 'xml':
            root = ET.Element('results')
            root.set('query', str(query))
            for image_name, value in results.items():
                image = ET.SubElement(root, 'image')
                image.set('name', str(image_name))
                #print(image)
                for app_name, info in value.items():
                    app = ET.SubElement(image, 'app')
                    for key, value in info.items():
                        app.set(str(key), str(value))
                    #print(app)
            text = ET.tostring(root, encoding="unicode")
            #print(text)
            #print('hi')
            return web.Response(text=text, content_type='text/xml')
        elif format == 'html':
            response = aiohttp_jinja2.render_template('index.j2',
                                              self.request,
                                              {})
            return response
        return web.Response(text="unknown format")

searchapp.add_routes(searchapp_routes)
