package pgt.cnv_view.util;

import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

import java.io.IOException;

public class Api {
    private static final String BASE_URL = "http://localhost:5000/api";

    private final OkHttpClient client = new OkHttpClient();

    private Response makeRequest(String endpoint, String method, RequestBody body) throws IOException {
        var builder = new Request.Builder()
                .url(BASE_URL + endpoint);
        switch (method.toUpperCase()) {
            case "POST":
                builder.post(body);
                break;
            case "PUT":
                builder.put(body);
                break;
            case "PATCH":
                builder.patch(body);
                break;
            case "DELETE":
                builder.delete();
                break;
            case "GET":
            default:
                builder.get();
                break;
        }

        var request =  builder.build();
        return client.newCall(request).execute();
    }

    public Response get(String endpoint) throws IOException {
        return makeRequest(endpoint, "GET", null);
    }

    public Response post(String endpoint, RequestBody body) throws IOException {
        return makeRequest(endpoint, "POST", body);
    }

    public Response put(String endpoint, RequestBody body) throws IOException {
        return makeRequest(endpoint, "PUT", body);
    }

    public Response delete(String endpoint) throws IOException {
        return makeRequest(endpoint, "DELETE", null);
    }

    public Response patch(String endpoint, RequestBody body) throws IOException {
        return makeRequest(endpoint, "PATCH", body);
    }

    private Api() { }

    public static class Holder {
        public static final Api INSTANCE = new Api();
    }
}
