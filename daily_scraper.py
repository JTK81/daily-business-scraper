# daily_scraper.py
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time

def scrape_bizbuysell():
    base_url = "https://www.bizbuysell.com/businesses-for-sale/?q=/Businesses-for-Sale/Midwest/"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(base_url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    listings = []

    for card in soup.select(".listing-card--details"):
        name = card.select_one(".listing-card--title")
        location = card.select_one(".listing-card--location")
        price = card.select_one(".listing-card--price")
        rev = card.select_one(".listing-card--gross")
        cash_flow = card.select_one(".listing-card--cashflow")
        url_tag = card.find("a", href=True)

        if not name or not rev or not cash_flow or not url_tag:
            continue

        state = ""
        if location and "," in location.text:
            state = location.text.split(",")[-1].strip()

        try:
            revenue = int(rev.text.replace("$", "").replace(",", "").strip())
            sde = int(cash_flow.text.replace("$", "").replace(",", "").strip())
        except:
            continue

        listing_url = "https://www.bizbuysell.com" + url_tag["href"]

        # Visit individual listing page for more details
        time.sleep(1)  # Be polite
        detail_resp = requests.get(listing_url, headers=headers)
        detail_soup = BeautifulSoup(detail_resp.text, "html.parser")

        industry = "Unknown"
        ffe = None
        listing_date = None

        try:
            details_section = detail_soup.select(".listing-summary__item")
            for item in details_section:
                label = item.select_one(".listing-summary__label")
                value = item.select_one(".listing-summary__value")
                if not label or not value:
                    continue
                label_text = label.text.strip()
                value_text = value.text.strip()

                if "FFE" in label_text:
                    ffe = int(value_text.replace("$", "").replace(",", ""))
                elif "Date" in label_text:
                    listing_date = value_text
                elif "Industry" in label_text:
                    industry = value_text
        except:
            pass

        listings.append({
            "Business Name": name.text.strip(),
            "Industry": industry,
            "State": state,
            "Revenue": revenue,
            "SDE": sde,
            "Cash Flow": sde,
            "FFE": ffe,
            "Asking Price": price.text.strip() if price else None,
            "Listing Date": listing_date,
            "URL": listing_url
        })

    return pd.DataFrame(listings)

def filter_data(df):
    allowed_industries = ["Services", "Manufacturing", "Transportation"]
    allowed_states = ["IL", "WI", "MI", "OH", "MN", "IN", "IA", "MO", "KS", "NE", "ND", "SD"]

    return df[
        (df["Industry"].isin(allowed_industries)) &
        (df["State"].isin(allowed_states)) &
        (df["Revenue"] >= 1_000_000) &
        (df["Revenue"] <= 5_000_000) &
        ((df["SDE"] / df["Revenue"]) >= 0.20)
    ]

def save_to_csv(df):
    today = datetime.now().strftime('%Y-%m-%d')
    filename = f"business_listings_{today}.csv"
    df.to_csv(filename, index=False)
    print(f"Saved: {filename}")

def main():
    df_raw = scrape_bizbuysell()
    df_filtered = filter_data(df_raw)
    save_to_csv(df_filtered)

if __name__ == "__main__":
    main()


