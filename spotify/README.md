# Blood Moon for Spotify

A [Spicetify](https://spicetify.app) theme: Blood Moon colors, Cinzel titles, square corners,
red progress bars and a red line above the player.

Install Spicetify first, then run `./install.sh spotify` from the repo root.

For the **Flatpak** version of Spotify, Spicetify needs write access to Spotify's files once:

```bash
sudo chmod a+wr /var/lib/flatpak/app/com.spotify.Client/x86_64/stable/active/files/extra/share/spotify
sudo chmod a+wr -R /var/lib/flatpak/app/com.spotify.Client/x86_64/stable/active/files/extra/share/spotify/Apps
```

The installer sets Spicetify's paths for the Flatpak automatically.

Spotify updates remove the theme. Run `spicetify backup apply` again afterwards.
