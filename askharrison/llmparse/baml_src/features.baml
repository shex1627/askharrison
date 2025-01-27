// This is a BAML config file, which extends the Jinja2 templating language to write LLM functions.

class FeatureList {
  featurelist NewFeature[] 
}

class Feature {
  title string
  summary string
  description string
}

class NewFeature {
  date string @description("date format of yyyy-mm-dd")
  features Feature[] @description("Extract the description of the feature")
}

function ExtractFeatures(resume_text: string) -> FeatureList {
  // see clients.baml
  client GPT4o

  // The prompt uses Jinja syntax. Change the models or this text and watch the prompt preview change!
  prompt #"
    Parse the following resume and return a structured representation of the data in the schema below.

    Resume:
    ---
    {{ resume_text }}
    ---

    {# special macro to print the output instructions. #}
    {{ ctx.output_format }}

    JSON:
  "#
}