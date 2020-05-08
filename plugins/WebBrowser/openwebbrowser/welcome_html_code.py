from openwebbrowser.css_code import *
from openwebbrowser.welcome_page_code import *

js_code = '''

document.oncontextmenu=function(e){return false;}

function NewProject() {
    Command.action('command:workbench.action.project.newProject');
}

function OpenProject() {
    Command.action('command:workbench.action.project.openProject');
}

function LoadNews(content) {
    document.getElementById("news").innerHTML = content
}

function LoadLearn(content) {
    document.getElementById("learn").innerHTML = content
}

function SetEmptyProject() {
    document.getElementById("welcome").classList.add("emptyRecent")
}

function LoadProjects(content) {
    document.getElementById("recent").innerHTML = content
}
'''

html_code = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>welcome</title>
    <meta name="renderer" content="webkit">
    {css_code}
</head>
<body>

<script type="text/javascript">
{js_code}
</script>
{content_code}
</body>
</html>
'''.format(css_code=css_code,content_code=content_code,js_code=js_code)
