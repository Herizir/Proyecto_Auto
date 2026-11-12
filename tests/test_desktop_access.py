import unittest

import customtkinter as ctk

from escritorio.app import MotorhausApp


class DesktopAccessTests(unittest.TestCase):
    def test_demo_replaces_access_screen_without_leaving_an_overlay(self):
        ctk.set_appearance_mode("light")
        app = MotorhausApp()
        self.addCleanup(app.destroy)
        app.update()

        for _ in range(2):
            app.show_access(True)
            app.show_access()
            app.update()
            access_container = app.access_container
            app.enter_demo()
            app.update()

            self.assertFalse(access_container.winfo_exists())
            self.assertTrue(app.sidebar.winfo_ismapped())
            self.assertTrue(app.main.winfo_ismapped())
            self.assertTrue(app.content.winfo_ismapped())
            self.assertEqual(app.current_page, "Resumen")
            self.assertEqual(len(app.winfo_children()), 2)


if __name__ == "__main__":
    unittest.main()
