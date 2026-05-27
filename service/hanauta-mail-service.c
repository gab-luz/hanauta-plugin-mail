#define _POSIX_C_SOURCE 200809L

#include <glib.h>
#include <glib/gstdio.h>

#include <stdlib.h>

typedef struct {
    gchar *plugin_root;
    gchar *checker_script;
    guint interval_seconds;
    guint source_id;
} MailService;

static MailService g_service = {0};

static gboolean run_checker_once(gpointer user_data) {
    (void)user_data;
    if (g_service.checker_script == NULL || !g_file_test(g_service.checker_script, G_FILE_TEST_EXISTS)) {
        g_warning("[hanauta-mail-service] checker script not found: %s", g_service.checker_script != NULL ? g_service.checker_script : "(null)");
        return TRUE;
    }

    gchar *argv[] = {"python3", g_service.checker_script, NULL};
    gchar *stdout_text = NULL;
    gchar *stderr_text = NULL;
    gint status = 0;
    GError *error = NULL;

    gboolean ok = g_spawn_sync(
        g_service.plugin_root,
        argv,
        NULL,
        G_SPAWN_SEARCH_PATH,
        NULL,
        NULL,
        &stdout_text,
        &stderr_text,
        &status,
        &error);

    if (!ok) {
        g_warning("[hanauta-mail-service] failed to run checker: %s", error != NULL ? error->message : "unknown error");
        g_clear_error(&error);
    } else if (status != 0) {
        g_warning("[hanauta-mail-service] checker exited with status %d", status);
    }

    g_free(stdout_text);
    g_free(stderr_text);
    return TRUE;
}

static void service_shutdown(void) {
    if (g_service.source_id != 0) {
        g_source_remove(g_service.source_id);
        g_service.source_id = 0;
    }
    g_clear_pointer(&g_service.checker_script, g_free);
    g_clear_pointer(&g_service.plugin_root, g_free);
}

int main(int argc, char **argv) {
    GMainLoop *loop = NULL;

    g_service.interval_seconds = 90;
    if (argc > 1) {
        gint parsed = (gint)g_ascii_strtoll(argv[1], NULL, 10);
        if (parsed >= 20 && parsed <= 3600) {
            g_service.interval_seconds = (guint)parsed;
        }
    }

    g_service.plugin_root = g_path_get_dirname(argv[0]);
    if (g_service.plugin_root == NULL) {
        g_service.plugin_root = g_get_current_dir();
    }

    if (!g_str_has_suffix(g_service.plugin_root, "/service")) {
        gchar *candidate = g_build_filename(g_service.plugin_root, "service", NULL);
        if (g_file_test(candidate, G_FILE_TEST_IS_DIR)) {
            g_free(g_service.plugin_root);
            g_service.plugin_root = g_path_get_dirname(candidate);
        }
        g_free(candidate);
    } else {
        gchar *root = g_path_get_dirname(g_service.plugin_root);
        g_free(g_service.plugin_root);
        g_service.plugin_root = root;
    }

    g_service.checker_script = g_build_filename(g_service.plugin_root, "scripts", "check_new_mail.py", NULL);

    g_message("[hanauta-mail-service] starting (interval=%u seconds)", g_service.interval_seconds);

    run_checker_once(NULL);
    g_service.source_id = g_timeout_add_seconds(g_service.interval_seconds, run_checker_once, NULL);

    loop = g_main_loop_new(NULL, FALSE);
    g_main_loop_run(loop);

    g_main_loop_unref(loop);
    service_shutdown();
    return EXIT_SUCCESS;
}
