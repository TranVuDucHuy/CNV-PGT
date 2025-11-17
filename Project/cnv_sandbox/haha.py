from huycnv import BaseInput, BaseOutput, AlgorithmPlugin, SampleBin, SampleSegment


class MyInput(BaseInput):
    pass


class MyOutput(BaseOutput):
    pass


class MyPlugin(AlgorithmPlugin):
    def run(self, input_data: MyInput, **kwargs) -> MyOutput:
        # Implement the algorithm logic here
        output_data = MyOutput(
            reference_genome="hg19",
            segments=[
                SampleSegment(
                    chromosome="1",
                    start=10000,
                    end=50000,
                    copy_number=3,
                    confidence=0.95,
                ),
                SampleSegment(
                    chromosome="2",
                    start=20000,
                    end=60000,
                    copy_number=2,
                    confidence=0.90,
                ),
            ],
            bins=[
                SampleBin(
                    chromosome="1",
                    start=10000,
                    end=10100,
                    read_count=50,
                    copy_number=3,
                    gc_content=0.42,
                ),
                SampleBin(
                    chromosome="2",
                    start=20000,
                    end=20100,
                    read_count=45,
                    copy_number=2,
                    gc_content=0.38,
                ),
            ],
        )
        return output_data
