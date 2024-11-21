import streamlit as st
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer
from elasticsearch import exceptions as es_exceptions
import re 

index_name = "all_movies"
model = SentenceTransformer('all-mpnet-base-v2')

try:
    
    es = Elasticsearch(
        "http://localhost:9200",
        basic_auth=("elastic", "DwOAtXZC3kMLCPadyoQY"),
        verify_certs=False,  
    )

    # Test connection
    if es.ping():
        
     st.image("C:/irwa Project_2/MovieBanner.png", use_column_width=True)  

    else:
        st.write("Failed to connect to Elasticsearch.")
except es_exceptions.ConnectionError as e:
    st.write(f"Error connecting to Elasticsearch: {e}")
except es_exceptions.AuthenticationException as e:
    st.write(f"Authentication failed: {e}")
except Exception as e:
    st.write(f"An unexpected error occurred: {e}")


def generate_movie_link(title):
    """Generates a formatted movie link from the title."""
    formatted_title = title.lower().replace("'", "")
    formatted_title = re.sub(r"[^\w]+", "_", formatted_title)
    formatted_title = re.sub(r"_+", "_", formatted_title)
    base_url = "https://www.rottentomatoes.com/m/"
    movie_link = f"{base_url}{formatted_title}"
    return movie_link


def search(input_keyword):
    # Step 1: Use the synonym analyzer on the input keyword
    try:
        analyzed_keyword = es.indices.analyze(index=index_name, body={
            "analyzer": "synonym_analyzer",
            "text": input_keyword
        })
    except Exception as e:
        st.write(f"Error during synonym analysis: {e}")
        return []
    
    # Step 2: Extract analyzed tokens from the synonym analyzer output
    processed_keyword = " ".join([token["token"] for token in analyzed_keyword["tokens"]])

    # Step 3: Encode the processed keyword using the model
    vector_of_input_keyword = model.encode(processed_keyword)

    
    query = {
        "field": "OverviewVector",
        "query_vector": vector_of_input_keyword,
        "k": 10,  # Top 10 results
        "num_candidates": 500
    }

    
    try:
        res = es.knn_search(index=index_name,
                            knn=query,
                            _source=["title", "overview", "genres", "vote_average", "poster_path", "backdrop_path"])
        results = res["hits"]["hits"]
        return results
    except Exception as e:
        st.write(f"An error occurred during search: {e}")
        return []


def search_movies(query):
    
    res = es.search(index="all_movies", body=query)
    return res

#bool function
def filter_movies(title=None, genres=None):
    
    bool_query = {
        "bool": {
            "must": []
        }
    }
   
    if title:
        bool_query["bool"]["must"].append({"match": {"title": title}})  
    if genres:
        bool_query["bool"]["must"].append({"match": {"genres": genres}})  

    
    query = {
        "query": bool_query
    }
    
    return search_movies(query)

#displaying part
def display_movie_details(result):
    """
    Display movie details including the poster image, backdrop image, title, description, genres, rating, and movie link.
    """
    try:
        
        title = result['_source'].get('title', 'Unknown Title')
        overview = result['_source'].get('overview', 'No description available.')
        genres = result['_source'].get('genres', 'No genre information available.')
        vote_average = result['_source'].get('vote_average', 'No rating available.')
        poster_path = result['_source'].get('poster_path', None)  


        
        movie_link = generate_movie_link(title)

        
        st.header(title)
        st.write(f"Description: {overview}")
        st.write(f"Genre: {genres}")
        st.write(f"Rating: {vote_average}")
        st.markdown(f"<a href='{movie_link}' style='color:#1f77b4;'>Rotten Tomatoes </a>", unsafe_allow_html=True)

        col1, col2 = st.columns([1, 2])  

        with col1:
            if poster_path:
                poster_url = f"https://image.tmdb.org/t/p/w600_and_h900_bestv2{poster_path}"
                
                st.image(poster_url, width=150) 
            else:
                st.write("No poster image available.")

        
        st.divider()
    except Exception as e:
        st.write(f"An error occurred while displaying the movie details: {e}")


def main():
    

    
    search_mode = st.radio("Select Search Mode:", ("Search movies by description", "Search movies by Title"))

    if search_mode == "Search movies by description":
       
        search_query = st.text_input("Enter a partial description of the movie")

       
        if st.button("Search"):
            if search_query:
               
                results = search(search_query)

                
             

                
                for result in results:
                    with st.container():
                        if '_source' in result:
                            display_movie_details(result)


    elif search_mode == "Search movies by Title":
       
        filter_title = st.text_input("Enter title to filter movies")
        filter_genres = st.text_input("Enter genres to filter movies")

        if st.button("Search"):
           
            filter_results = filter_movies(title=filter_title, genres=filter_genres)

            

            for result in filter_results['hits']['hits']:
                with st.container():
                    if '_source' in result:
                        display_movie_details(result)



if __name__ == "__main__":
    main()
