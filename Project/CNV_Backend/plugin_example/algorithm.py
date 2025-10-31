from algorithm import AlgorithmPlugin, BaseInput, BaseOutput

class InputClass(BaseInput):
    haha: str

class OutputClass(BaseOutput):
    result: str
    something_in_kwargs: str = "default value"

class ExeClass(AlgorithmPlugin):
    def run(self, input_data: InputClass, **kwargs) -> OutputClass: 
        output = OutputClass(segments=[], result=f"Received: {input_data.haha}", something_in_kwargs=kwargs.get("extra_info", "no extra info"))
        return output
    
