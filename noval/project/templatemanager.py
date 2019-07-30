# -*- coding: utf-8 -*-
import noval.util.singleton as singleton

@singleton.Singleton
class ProjectTemplateManager:
    """description of class"""


    def __init__(self):
        #项目模板列表,存在先后顺序
        self.project_templates = []
                
    def AddProjectTemplate(self,template_catlog,template_name,pages):
        if template_catlog.find(' ') != -1:
            raise RuntimeError("catlog could not contain blank character")
        project_template = self.FindProjectTemplate(template_catlog)
        if not project_template:
            self.project_templates.append({template_catlog:[(template_name,pages),]})
        else:
            project_template[template_catlog].extend([(template_name,pages),])

    def FindProjectTemplate(self,template_catlog):
        for project_template in self.project_templates:
            if list(project_template.keys())[0] == template_catlog:
                return project_template
        return None
            
    @property
    def ProjectTemplates(self):
        return self.project_templates