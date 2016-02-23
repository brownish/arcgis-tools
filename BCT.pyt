import os
import arcpy


class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Toolbox"
        self.alias = ""

        # List of tool classes associated with this toolbox
        self.tools = [SummarizeTables]


class SummarizeTables(object):
    def __init__(self):
        self.label = "Summarize Tables"
        self.description = "This tool summarizes multiple fields by a single key field, then finds the value " \
                           "with the highest percentage (percentage field), writing that row to a new table. " \
                           "The output is a table with one row per key value, its corresponding percentage, " \
                           "and the variable value."
        self.category = "Utilities"
        self.canRunInBackground = False

    def getParameterInfo(self):
        # Define Parameters
        input_table = arcpy.Parameter(
            displayName="Input Table",
            name="input_table",
            datatype="DETable",
            parameterType="Required",
            direction="Input")
        input_table.value = r'C:\Users\archadmin\projects\arcgis-tools\temp\beth.gdb\geomorph'

        output_workspace = arcpy.Parameter(
            displayName="Output Workspace",
            name="output_workspace",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input")
        output_workspace.value = r'C:\Users\archadmin\projects\arcgis-tools\temp\beth.gdb'

        variable_fields = arcpy.Parameter(
            displayName="Variable Fields",
            name="variable_fields",
            datatype="GPString",
            multiValue=True,
            parameterType="Required",
            direction="Input")

        variable_fields.parameterDependencies = [input_table.name]
        variable_fields.filter.type = 'ValueList'
        variable_fields.filter.list = []

        key_field = arcpy.Parameter(
            displayName="Key Field",
            name="key_field",
            datatype="GPString",
            parameterType="Required",
            direction="Input")

        key_field.value = 'mukey'
        key_field.parameterDependencies = [input_table.name]
        key_field.filter.type = 'ValueList'
        key_field.filter.list = []

        percentage_field = arcpy.Parameter(
            displayName="Percentage Field",
            name="percentage_field",
            datatype="GPString",
            parameterType="Required",
            direction="Input")

        percentage_field.value = 'comppct_r'
        percentage_field.parameterDependencies = [input_table.name]
        percentage_field.filter.type = 'ValueList'
        percentage_field.filter.list = []

        null_value = arcpy.Parameter(
            displayName="Null Value",
            name="null_value",
            datatype="GPString",
            parameterType="Optional",
            direction="Input")
        null_value.value = 'No Data'
        exclude_null = arcpy.Parameter(
            displayName="Exclude Null Values?",
            name="exclude_null",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input")

        params = [input_table, output_workspace, variable_fields, key_field, percentage_field, null_value, exclude_null]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        if parameters[0].value and parameters[0].altered:
            tbl = parameters[0].value
            desc = arcpy.Describe(tbl)
            fields = desc.fields
            filter_list = [f.name for f in fields]
            parameters[2].filter.list = filter_list
            parameters[3].filter.list = filter_list
            parameters[4].filter.list = filter_list

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        input_table = parameters[0].valueAsText
        output_workspace = parameters[1].valueAsText
        variable_fields = parameters[2].valueAsText
        key_field = parameters[3].valueAsText
        percentage_field = parameters[4].valueAsText
        null_value = parameters[5].valueAsText
        exclude_null = parameters[6].valueAsText

        variables = variable_fields.split(';')
        sum_percentage_field = "SUM_" + percentage_field  # Name of summed percentage field
        max_sum_percentage_field = "MAX_" + sum_percentage_field  # Name of Max percentage field

        messages.addMessage(input_table)
        messages.addMessage(output_workspace)
        messages.addMessage(variable_fields)
        messages.addMessage(key_field)
        messages.addMessage(percentage_field)
        messages.addMessage(null_value)
        messages.addMessage(exclude_null)
        messages.addMessage(sum_percentage_field)
        messages.addMessage(max_sum_percentage_field)

        messages.addMessage("Beginning Calculations!")
        
        for var in variables:
            arcpy.AddMessage("--------------------")
            arcpy.AddMessage("%s %s" % ("Starting", var))

            table_view = "table_view"
            if exclude_null == "true":
                table_query = 'NOT "' + var + '" = ' "'" + null_value + "'"
                arcpy.AddMessage("%s (%s)" % ("Excluding Nulls:", table_query))
            else:
                arcpy.AddMessage("Not excluding nulls")
                table_query = ""
        
            arcpy.AddMessage("%s %s %s" %("Making", "table", "view"))
            arcpy.MakeTableView_management(input_table, table_view, table_query)
            temp_table = os.path.join("in_memory", "TEMP" + var)  # Temp table location and name
            output_table = os.path.join(output_workspace, "SUM_" + var)  # Output table location and name
        
            # CHECK IF THE OUTPUT TABLE EXISTS, IF IT DOES, DELETE IT/RENAME IT
        
            if arcpy.Exists(temp_table):
                arcpy.AddMessage("%s: %s, %s!" % ("Found", temp_table, "deleting"))
                arcpy.Delete_management(temp_table)
            else:
                pass
            if arcpy.Exists(output_table):
                arcpy.AddMessage("%s: %s, %s %s!" % ("Found", output_table, "skipping", var))
                continue
            else:
                pass
        
            arcpy.AddMessage("%s %s %s %s %s" % ("Summarizing", var, percentage_field, "by", key_field))
            arcpy.Statistics_analysis(table_view, temp_table, [[percentage_field, "SUM"]], [key_field, var])
        
            arcpy.AddMessage("%s %s" % ("Finding maximum", var))
            arcpy.Statistics_analysis(temp_table, output_table, [[sum_percentage_field, "MAX"]], [key_field])
            arcpy.DeleteField_management(output_table, "FREQUENCY")

            join_field = "joinfield"
            temp_join_expression = '!' + key_field + '! + "_" + str(!' + sum_percentage_field + '!)'
            final_join_expression = '!' + key_field + '! + "_" + str(!' + max_sum_percentage_field + '!)'
        
            arcpy.AddMessage("Adding necessary join fields")
            arcpy.AddField_management(output_table, join_field, "String")
            arcpy.AddField_management(temp_table, join_field, "String")
        
            arcpy.AddMessage("Calculating join fields")
            arcpy.CalculateField_management(output_table, join_field, final_join_expression, "PYTHON")
            arcpy.CalculateField_management(temp_table, join_field, temp_join_expression, "PYTHON")
        
            arcpy.AddMessage("Joining values to final table")
            arcpy.JoinField_management(output_table, join_field, temp_table, join_field, [var])
        
            arcpy.AddMessage("Creating Relationship Class")
            output_relationship_path = os.path.join(output_workspace,
                                                    os.path.basename(output_table) + "_" + os.path.basename(input_table))
            forward_label = var + " > " + os.path.basename(input_table)
            backward_label = os.path.basename(input_table) + " > " + var
            arcpy.CreateRelationshipClass_management(output_table, input_table, output_relationship_path, "SIMPLE",
                                                     forward_label, backward_label, "#", "#", "#", key_field, key_field)
        
            arcpy.AddMessage("Cleaning up temporary tables")
            arcpy.DeleteField_management(output_table, join_field)
            arcpy.Delete_management(temp_table)
            arcpy.Delete_management(table_view)


        return
