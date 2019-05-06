import noval.util.singleton as singleton

@singleton.Singleton
class ProjectTemplateManager:
    """description of class"""


    def __init__(self):
        self.project_templates = {
        }
                
    def AddProjectTemplate(self,template_catlog,template_name,pages):
        
        if template_catlog.find(' ') != -1:
            raise RuntimeError("catlog could not contain blank character")

        if template_catlog not in self.project_templates:
            self.project_templates[template_catlog] = [(template_name,pages),]
        else:
            self.project_templates[template_catlog].extend([(template_name,pages),])
            
    @property
    def ProjectTemplates(self):
        return self.project_templates