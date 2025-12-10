from models import Commit

# to keep evry changes without loses we must separate intentions of mutations

class CommitSplitter:



    def split(self, commit: Commit) -> list[Commit]:
        ...