import chromadb
from yt_fts.config import get_or_make_chroma_path

def main():
    chroma_path = get_or_make_chroma_path() 
    view_collections(chroma_path)

def view_collections(chroma_path):
    chroma_client = chromadb.PersistentClient(path=chroma_path)
    collection = chroma_client.get_collection(name="subEmbeddings")
    # print(collection.peek())
    print(collection.count())


if __name__ == "__main__":
    main()